"""Step 3 — Run the 3-condition evaluation.

Prerequisites:
  - MnemeBrain backend running at http://localhost:8000
  - Brain loaded via step 2
  - ollama pull mistral
  - ollama pull llama3.1:70b  (or use Groq — see USE_GROQ below)
  - test.json from step 1
"""

import json
import os

import ollama
from tqdm import tqdm

from mnemebrain import Brain

# -- Configuration --------------------------------------------------------
MNEMEBRAIN_URL = "http://localhost:8000"
USE_GROQ = os.environ.get("USE_GROQ", "").lower() in ("1", "true", "yes")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-70b-versatile"
N = 50  # number of test questions
# -------------------------------------------------------------------------

with open("test.json") as f:
    test = json.load(f)

brain = Brain(agent_id="experiment-7b", base_url=MNEMEBRAIN_URL)


# -- Metric ---------------------------------------------------------------
def exact_match(prediction: str, answer: str) -> bool:
    """Relaxed exact match — handles 'George Orwell' vs 'Orwell'."""
    pred = prediction.lower().strip(". ")
    ans = answer.lower().strip(". ")
    return pred == ans or ans in pred or pred in ans


# -- Condition A: 7B alone (no memory) ------------------------------------
def ask_7b_plain(question: str) -> str:
    response = ollama.chat(model="mistral", messages=[{
        "role": "user",
        "content": f"Answer this question in one short phrase: {question}"
    }])
    return response["message"]["content"].strip()


# -- Condition B: 7B + MnemeBrain -----------------------------------------
def ask_7b_with_brain(question: str) -> str:
    result = brain.ask(
        question=question,
        query_type="FACTUAL",
        agent_id="experiment-7b",
    )

    context = "\n".join([b.claim for b in result.retrieved_beliefs[:3]])

    response = ollama.chat(model="mistral", messages=[{
        "role": "user",
        "content": f"""Use the following context to answer the question.
Answer in one short phrase only.

Context:
{context}

Question: {question}

Answer:"""
    }])

    answer = response["message"]["content"].strip()
    brain.feedback(result.query_id, outcome="COMPLETED")
    return answer


# -- Condition C: 70B alone (no memory) -----------------------------------
def ask_70b_plain(question: str) -> str:
    if USE_GROQ:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                "role": "user",
                "content": f"Answer this question in one short phrase: {question}"
            }],
        )
        return response.choices[0].message.content.strip()
    else:
        response = ollama.chat(model="llama3.1:70b", messages=[{
            "role": "user",
            "content": f"Answer this question in one short phrase: {question}"
        }])
        return response["message"]["content"].strip()


# -- Run all 3 conditions -------------------------------------------------
results = {"7b_plain": [], "7b_mnemebrain": [], "70b_plain": []}

print(f"\nCondition A: 7B (no memory) — {N} questions")
for sample in tqdm(test[:N]):
    pred = ask_7b_plain(sample["question"])
    results["7b_plain"].append({
        "question": sample["question"], "answer": sample["answer"],
        "prediction": pred, "correct": exact_match(pred, sample["answer"])
    })

print(f"\nCondition B: 7B + MnemeBrain — {N} questions")
for sample in tqdm(test[:N]):
    pred = ask_7b_with_brain(sample["question"])
    results["7b_mnemebrain"].append({
        "question": sample["question"], "answer": sample["answer"],
        "prediction": pred, "correct": exact_match(pred, sample["answer"])
    })

print(f"\nCondition C: 70B (no memory) — {N} questions")
for sample in tqdm(test[:N]):
    pred = ask_70b_plain(sample["question"])
    results["70b_plain"].append({
        "question": sample["question"], "answer": sample["answer"],
        "prediction": pred, "correct": exact_match(pred, sample["answer"])
    })

# -- Results ---------------------------------------------------------------
print("\n" + "=" * 55)
print("RESULTS")
print("=" * 55)
for key, data in results.items():
    correct = sum(d["correct"] for d in data)
    score = correct / len(data) * 100
    label = {
        "7b_plain":      "7B alone          ",
        "7b_mnemebrain": "7B + MnemeBrain   ",
        "70b_plain":     "70B alone         "
    }[key]
    print(f"  {label}: {score:.1f}%  ({correct}/{len(data)})")
print("=" * 55)

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nFull results saved to results.json")
