#!/usr/bin/env python
"""
Build search_review/eecs_queries.csv for the CS/EE department retrieval notebook.

Expected output format:
    query_id,query_text

Run from the same folder as the notebook:
    python build_eecs_queries.py

Optional:
    python build_eecs_queries.py --output search_review/eecs_queries.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


DEFAULT_EECS_QUERIES = [
    {
        "query_id": "q01",
        "query_text": (
            "Find artificial intelligence certificate forms, certificate worksheets, "
            "program applications, professional AI certificate documents, and related AI certificate requirements."
        ),
    },
    {
        "query_id": "q02",
        "query_text": (
            "Find artificial intelligence minor forms, AI minor worksheets, minor program applications, "
            "and requirements for students completing an AI minor."
        ),
    },
    {
        "query_id": "q03",
        "query_text": (
            "Find big data analytics certificate forms, professional big data analytics certificate worksheets, "
            "applications, and related big data analytics program requirements."
        ),
    },
    {
        "query_id": "q04",
        "query_text": (
            "Find MS Computer Science program worksheets, MS CSE worksheet documents, professional MS CS worksheets, "
            "and computer science graduate program requirements."
        ),
    },
    {
        "query_id": "q05",
        "query_text": (
            "Find MS Computer Engineering program sheets, MS COEN worksheets, computer engineering application forms, "
            "and computer engineering graduate requirements."
        ),
    },
    {
        "query_id": "q06",
        "query_text": (
            "Find MS Electrical Engineering worksheets, EEL program sheets, electrical engineering graduate program information, "
            "and electrical engineering degree requirements."
        ),
    },
    {
        "query_id": "q07",
        "query_text": (
            "Find cybersecurity certificate and minor documents, cyber security worksheets, cybersecurity applications, "
            "and security-related courses such as cryptography, network security, and data security."
        ),
    },
    {
        "query_id": "q08",
        "query_text": (
            "Find data science and analytics certificate documents, DSA concentration worksheets, CSDA or computer science data analytics "
            "program sheets, and related data science courses."
        ),
    },
    {
        "query_id": "q09",
        "query_text": (
            "Find machine learning, artificial intelligence, neural networks, deep learning, computer vision, and NLP course syllabi."
        ),
    },
    {
        "query_id": "q10",
        "query_text": (
            "Find data mining, information retrieval, web mining, big data analytics, and database-related course syllabi."
        ),
    },
    {
        "query_id": "q11",
        "query_text": (
            "Find software engineering courses and syllabi covering software requirements engineering, software testing, "
            "software architecture, software maintenance, and object-oriented design."
        ),
    },
    {
        "query_id": "q12",
        "query_text": (
            "Find electrical engineering course syllabi for circuits, electronics, signal processing, communications, "
            "control systems, antennas, RF, power systems, and smart grid topics."
        ),
    },
    {
        "query_id": "q13",
        "query_text": (
            "Find computer architecture, digital logic, microprocessor, embedded systems, VLSI, and computer design course syllabi."
        ),
    },
    {
        "query_id": "q14",
        "query_text": (
            "Find general EECS student forms and administrative documents such as audit forms, application forms, "
            "graduate pathway scholarships, low residency PhD forms, and conflict of interest disclosure forms."
        ),
    },
]


def build_queries(output_path: Path) -> pd.DataFrame:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    queries_df = pd.DataFrame(DEFAULT_EECS_QUERIES)

    # Keep deterministic ordering and template-compatible dtypes.
    queries_df = queries_df[["query_id", "query_text"]]
    queries_df.to_csv(output_path, index=False)

    print(f"Saved {len(queries_df)} queries to: {output_path}")
    print(queries_df.to_string(index=False))
    return queries_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Create EECS queries.csv for retrieval evaluation.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("search_review/eecs_queries.csv"),
        help="Output CSV path. Default: search_review/eecs_queries.csv",
    )
    args = parser.parse_args()
    build_queries(args.output)


if __name__ == "__main__":
    main()
