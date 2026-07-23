#!/usr/bin/env python
"""
Validate EECS retrieval evaluation files.

Checks:
    - data/corpus.csv has doc_id,text
    - search_review/eecs_queries.csv has query_id,query_text
    - search_review/eecs_qrels.csv has query_id,doc_id,relevance
    - all qrel query_ids exist in queries.csv
    - all qrel doc_ids exist in corpus.csv
    - relevance is 0, 1, or 2
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def validate_files(corpus_path: Path, queries_path: Path, qrels_path: Path) -> None:
    corpus = pd.read_csv(corpus_path).fillna("")
    queries = pd.read_csv(queries_path).fillna("")
    qrels = pd.read_csv(qrels_path).fillna("")

    required = {
        str(corpus_path): {"doc_id", "text"},
        str(queries_path): {"query_id", "query_text"},
        str(qrels_path): {"query_id", "doc_id", "relevance"},
    }
    frames = {
        str(corpus_path): corpus,
        str(queries_path): queries,
        str(qrels_path): qrels,
    }

    for name, cols in required.items():
        missing = cols - set(frames[name].columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")

    query_ids = set(queries["query_id"].astype(str))
    doc_ids = set(corpus["doc_id"].astype(str))

    qrel_query_ids = set(qrels["query_id"].astype(str))
    qrel_doc_ids = set(qrels["doc_id"].astype(str))

    unknown_queries = sorted(qrel_query_ids - query_ids)
    unknown_docs = sorted(qrel_doc_ids - doc_ids)

    if unknown_queries:
        raise ValueError(f"qrels contains query_ids not in queries.csv: {unknown_queries[:20]}")
    if unknown_docs:
        raise ValueError(f"qrels contains doc_ids not in corpus.csv: {unknown_docs[:20]}")

    relevance_values = set(pd.to_numeric(qrels["relevance"], errors="coerce").dropna().astype(int))
    bad_rels = sorted(relevance_values - {0, 1, 2})
    if bad_rels:
        raise ValueError(f"qrels has unsupported relevance values: {bad_rels}")

    print("Validation passed.")
    print(f"Corpus documents: {len(corpus)}")
    print(f"Queries: {len(queries)}")
    print(f"Qrel rows: {len(qrels)}")
    print("\nQrels per query:")
    print(qrels.groupby("query_id").size().to_string())
    print("\nRelevance distribution:")
    print(qrels["relevance"].value_counts().sort_index().to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate EECS corpus, queries, and qrels CSV files.")
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus.csv"))
    parser.add_argument("--queries", type=Path, default=Path("search_review/eecs_queries.csv"))
    parser.add_argument("--qrels", type=Path, default=Path("search_review/eecs_qrels.csv"))
    args = parser.parse_args()

    validate_files(args.corpus, args.queries, args.qrels)


if __name__ == "__main__":
    main()
