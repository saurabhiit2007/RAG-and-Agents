# TF-IDF Reference

TF-IDF (Term Frequency–Inverse Document Frequency) is the precursor to BM25. It is rarely used directly in production RAG — know it as the baseline BM25 improves upon.

## Formula

```
TF(t, d)      = count(t in d) / total terms in d
IDF(t)        = log(N / (1 + df(t)))
TF-IDF(t, d)  = TF(t, d) × IDF(t)
```

## Why BM25 Replaced It

| Weakness | BM25 Fix |
|---|---|
| TF grows linearly — keyword stuffing raises score | Saturating TF with k₁ parameter |
| No length normalisation — longer docs score higher | Explicit length normalisation via b parameter |
| IDF formula unstable for very rare/common terms | Modified IDF: log((N − df + 0.5)/(df + 0.5)) |

> For RAG interviews: know TF-IDF as context for why BM25 exists, not as a standalone topic. See [BM25](bm25.md) and [Retrieval Methods](../retrieval_methods.md).
