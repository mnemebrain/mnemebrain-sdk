# Proof the Claim: 7B + MnemeBrain vs 70B

> "A 7B model with the right memory architecture can outperform a 70B model on knowledge-intensive tasks."

## Overview

This experiment uses the MnemeBrain Python SDK to demonstrate that structured belief memory can compensate for model scale. A 7B model (Mistral) augmented with MnemeBrain outperforms a 70B model (Llama 3.1) on HotpotQA multi-hop question answering.

## 3-Condition Design

| Condition | Model | Memory | Purpose |
|-----------|-------|--------|---------|
| A | Mistral 7B | None | Raw model baseline |
| B | Mistral 7B | MnemeBrain | Memory-augmented |
| C | Llama 3.1 70B | None | Scale baseline |

## Running the Experiment

### Prerequisites

```bash
# Install the SDK with experiment extras
pip install mnemebrain[experiment]

# Pull Ollama models
ollama pull mistral
ollama pull llama3.1:70b  # or use Groq free tier

# Start MnemeBrain backend
cd mnemebrain-lite && uv run python -m mnemebrain_core
```

### Step 1: Download Data

```bash
cd examples/proof_the_claim
python 1_download_data.py
# Creates train.json (150 samples) and test.json (50 samples)
```

### Step 2: Load Knowledge

```bash
python 2_load_brain.py
# Loads training contexts into MnemeBrain as structured beliefs
```

### Step 3: Evaluate

```bash
python 3_evaluate.py
# Runs all 3 conditions on 50 held-out test questions
```

Using Groq instead of local 70B:
```bash
USE_GROQ=1 GROQ_API_KEY=gsk_... python 3_evaluate.py
```

## How It Works

1. **Training data** is loaded into MnemeBrain as structured beliefs with evidence provenance
2. **Test questions** are held out — the brain never saw them
3. **Condition B** uses `brain.ask()` to retrieve relevant beliefs, then feeds them as context to Mistral 7B
4. The 70B model must answer from parametric knowledge alone

## Expected Results

```
=====================================================
RESULTS
=====================================================
  7B alone          :  ~20%
  7B + MnemeBrain   :  ~50%
  70B alone         :  ~40%
=====================================================
```

## Key Insight

The 70B stores knowledge in weights at training time. The 7B retrieves structured beliefs at runtime — with evidence chains and confidence scores. Different bottlenecks, different solutions.

## References

- **HippoRAG** (NeurIPS 2024) — graph-based retrieval +20% on multi-hop QA
- **RAG** (Lewis et al., 2020) — retrieval-augmented models outperform larger parametric-only models
- **Titans** (Google Research, NeurIPS 2025) — smaller models with neural long-term memory outperform larger vanilla Transformers
