"""Ranking functions used by Second Brain. Ranks start at one."""
import re


def tokenize_query(text):
    return re.sub(r'[^\w\s]',' ',text).lower().split()

def rrf_fuse(vec_ranks,fts_ranks,k=60,absent_rank=41):
    scored=[(mid,1/(k+vec_ranks.get(mid,absent_rank))+1/(k+fts_ranks.get(mid,absent_rank)))
            for mid in vec_ranks.keys()|fts_ranks.keys()]
    return sorted(scored,key=lambda item:(-item[1],item[0]))


OVERLAP_PREFIX_MIN = 4


def token_overlap(query_tokens, doc_tokens) -> float:
    """Fraction of query tokens present in ``doc_tokens``.

    A query token counts as present when an identical token exists, or when a
    doc token and the query token share a prefix relationship and the shorter
    of the two is at least ``OVERLAP_PREFIX_MIN`` characters — a cheap,
    stemmer-free way to tolerate inflection ("skim"/"skimmed", "stage"/"stages")
    that the full-text leg already tolerates through its stemmer. Exact matches
    are checked first, so the O(query × doc) prefix scan runs only for tokens
    that missed.
    """
    if not query_tokens:
        return 0.0
    hits = 0
    for q in query_tokens:
        if q in doc_tokens:
            hits += 1
            continue
        if len(q) >= OVERLAP_PREFIX_MIN and any(
            (t.startswith(q)) or (len(t) >= OVERLAP_PREFIX_MIN and q.startswith(t)) for t in doc_tokens
        ):
            hits += 1
    return hits / len(query_tokens)
