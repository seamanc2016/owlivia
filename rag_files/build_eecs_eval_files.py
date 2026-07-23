#!/usr/bin/env python
"""
Build the EECS retrieval evaluation starter CSVs in search_review/.

Created files by default:
    search_review/eecs_queries.csv
    search_review/eecs_qrels.csv
    search_review/eecs_qrels_review.csv

The retrieval notebook can now read these files directly from search_review/.
For older versions of the notebook that still expect data/queries.csv and
 data/qrels.csv, pass --sync-template-data to also copy the first two files there.

Run from the same folder as the notebook after data/corpus.csv exists:
    python build_eecs_eval_files.py

Optional compatibility copy:
    python build_eecs_eval_files.py --sync-template-data
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from build_eecs_queries import build_queries
from build_eecs_qrels import build_qrels


DEFAULT_REVIEW_DIR = Path("search_review")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build EECS queries, qrels, and qrels-review CSVs under search_review/."
    )
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus.csv"), help="Input corpus CSV.")
    parser.add_argument(
        "--review-dir",
        type=Path,
        default=DEFAULT_REVIEW_DIR,
        help="Folder for starter evaluation CSVs. Default: search_review",
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=None,
        help="Optional explicit queries CSV path. Default: search_review/eecs_queries.csv",
    )
    parser.add_argument(
        "--qrels",
        type=Path,
        default=None,
        help="Optional explicit qrels CSV path. Default: search_review/eecs_qrels.csv",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=None,
        help="Optional explicit review CSV path. Default: search_review/eecs_qrels_review.csv",
    )
    parser.add_argument(
        "--sync-template-data",
        action="store_true",
        help="Also copy eecs_queries.csv to data/queries.csv and eecs_qrels.csv to data/qrels.csv for older templates.",
    )
    args = parser.parse_args()

    review_dir = args.review_dir
    review_dir.mkdir(parents=True, exist_ok=True)

    queries_path = args.queries or (review_dir / "eecs_queries.csv")
    qrels_path = args.qrels or (review_dir / "eecs_qrels.csv")
    review_output_path = args.review_output or (review_dir / "eecs_qrels_review.csv")

    build_queries(queries_path)
    build_qrels(
        corpus_path=args.corpus,
        queries_path=queries_path,
        output_path=qrels_path,
        review_output_path=review_output_path,
    )

    if args.sync_template_data:
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(queries_path, data_dir / "queries.csv")
        shutil.copy2(qrels_path, data_dir / "qrels.csv")
        print("\nCompatibility copies written:")
        print(f"  {data_dir / 'queries.csv'}")
        print(f"  {data_dir / 'qrels.csv'}")

    print("\nEECS evaluation starter files are ready:")
    print(f"  Queries:      {queries_path}")
    print(f"  Qrels:        {qrels_path}")
    print(f"  Review file:  {review_output_path}")


if __name__ == "__main__":
    main()
