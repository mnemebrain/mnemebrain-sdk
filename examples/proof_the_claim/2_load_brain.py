"""Step 2 — Load knowledge from the training set into MnemeBrain.

Prerequisites:
  - MnemeBrain backend running at http://localhost:8000
  - pip install mnemebrain (this SDK)
  - train.json from step 1
"""

import json
import sys
from tqdm import tqdm

from mnemebrain import Brain

MNEMEBRAIN_URL = "http://localhost:8000"

with open("train.json") as f:
    train = json.load(f)

brain = Brain(agent_id="experiment-7b", base_url=MNEMEBRAIN_URL)

print("Loading knowledge into MnemeBrain from training set...")

loaded = 0
errors = 0
for i, sample in enumerate(tqdm(train)):
    for title, sentences in zip(
        sample["context"]["title"],
        sample["context"]["sentences"]
    ):
        claim = f"{title}: {' '.join(sentences)}"
        try:
            brain.believe(
                claim=claim,
                evidence=[f"hotpotqa_train_{i}_{title}"],
                confidence=0.9,
                belief_type="fact",
            )
            loaded += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"\n  Error loading claim {i}: {e}", file=sys.stderr)

print(f"\nBrain loaded: {loaded} beliefs from {len(train)} training samples")
if errors:
    print(f"  ({errors} errors)")
print("Brain will now answer questions it has never seen.")
