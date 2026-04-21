# SPLADE Reference

SPLADE is covered in depth in [Retrieval Methods](../retrieval_methods.md). This page is a compact math and mechanics reference.

## Scoring Function

```
Score(t) = max_over_positions [ log(1 + ReLU(logit_t)) ]
```

- **ReLU** — removes negative scores (enforces non-negativity)
- **log(1 + x)** — compresses large activations, controls sparsity
- **max pooling** — takes the highest score across all token positions for term t

## Pipeline at a Glance

```
Input text
  → BERT/MLM encoder
  → For each token position: score all V vocabulary terms
  → ReLU + log + max-pool across positions
  → Sparse vector {term: weight, ...}  (most weights = 0)
  → Store in standard inverted index
```

## Term Expansion Example

| Input | Active terms after expansion |
|---|---|
| `"car repair"` | car, repair, automobile, mechanic, engine, maintenance |
| `"better search models"` | search, retrieval, ranking, model, information, query |

Documents containing `"automobile maintenance"` match query `"car repair"` even with zero word overlap.

## SPLADE vs BM25 vs Dense

| | BM25 | SPLADE | Dense bi-encoder |
|---|---|---|---|
| Term weights | Hand-crafted formula | Learned by transformer | N/A (dense vector) |
| Semantic expansion | None | Yes (learned) | Implicit |
| Index type | Inverted index | Inverted index | Vector index (ANN) |
| Training needed | No | Yes | Yes |
| Interpretable | High | Moderate | Low |

> Mental model: **SPLADE = BM25 with neural term weights and learned vocabulary expansion.**
