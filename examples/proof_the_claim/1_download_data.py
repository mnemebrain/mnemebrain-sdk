"""Step 1 — Download HotpotQA data and split into train/test sets."""

from datasets import load_dataset
import json

dataset = load_dataset("hotpot_qa", "distractor", split="validation[:200]")

samples = [{
    "question": d["question"],
    "answer":   d["answer"],
    "context":  d["context"]
} for d in dataset]

# Train/test split — load brain from train, evaluate on test
# This prevents memory contamination (leakage)
train_samples = samples[:150]
test_samples  = samples[150:200]   # 50 held-out questions

with open("train.json", "w") as f:
    json.dump(train_samples, f, indent=2)

with open("test.json", "w") as f:
    json.dump(test_samples, f, indent=2)

print(f"Train: {len(train_samples)} samples")
print(f"Test:  {len(test_samples)} samples")
