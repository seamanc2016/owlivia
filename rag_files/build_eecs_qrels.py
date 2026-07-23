#!/usr/bin/env python
"""
Build qrels.csv for the CS/EE department retrieval notebook.

Expected input:
    data/corpus.csv with at least:
        doc_id,text
    search_review/eecs_queries.csv with:
        query_id,query_text

Expected output:
    search_review/eecs_qrels.csv with:
        query_id,doc_id,relevance

Relevance labels:
    2 = strong/primary match for the query
    1 = partial/secondary match for the query
    0 = not written to qrels.csv

This is a weak-supervision generator. It is meant to create a useful first qrels
file for testing BM25, FAISS, and RRF performance. For a final report, open
search_review/eecs_qrels_review.csv and manually check the labels.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class QueryRule:
    """Rule set used to label candidate relevant documents for one query."""
    query_id: str
    strong: tuple[str, ...] = field(default_factory=tuple)
    medium: tuple[str, ...] = field(default_factory=tuple)
    weak: tuple[str, ...] = field(default_factory=tuple)
    exclude: tuple[str, ...] = field(default_factory=tuple)
    require_any: tuple[str, ...] = field(default_factory=tuple)
    max_per_query: int = 30


def norm(text: object) -> str:
    """Normalize text for case-insensitive regex matching."""
    text = "" if pd.isna(text) else str(text)
    text = text.replace("\x00", " ")
    text = re.sub(r"[_\-\/]+", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def regex_hit(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def count_hits(patterns: Iterable[str], text: str) -> int:
    return sum(1 for pattern in patterns if regex_hit(pattern, text))


# These qids match build_eecs_queries.py.
# Patterns are intentionally redundant because filenames, titles, metadata, and PDF text vary.
QUERY_RULES: dict[str, QueryRule] = {
    "q01": QueryRule(
        query_id="q01",
        strong=(
            r"artificial intelligence certificate",
            r"certificate artificial intelligence",
            r"\bai certificate\b",
            r"professional certificate ai",
            r"professional ai certificate",
            r"certificate.*artificial intelligence",
            r"artificial intelligence.*certificate",
        ),
        medium=(
            r"artificial intelligence",
            r"\bai\b",
            r"certificate",
            r"worksheet",
            r"program application",
            r"program worksheet",
            r"cap\s*4630",
            r"cap\s*6635",
        ),
        weak=(r"machine learning", r"deep learning", r"neural networks", r"nlp"),
        require_any=(r"artificial intelligence", r"\bai\b", r"cap\s*4630", r"cap\s*6635"),
    ),
    "q02": QueryRule(
        query_id="q02",
        strong=(
            r"artificial intelligence minor",
            r"\bai minor\b",
            r"minor artificial intelligence",
            r"minor.*artificial intelligence",
            r"artificial intelligence.*minor",
        ),
        medium=(r"minor", r"worksheet", r"program application", r"artificial intelligence", r"\bai\b"),
        weak=(r"certificate", r"program worksheet"),
        require_any=(r"minor",),
    ),
    "q03": QueryRule(
        query_id="q03",
        strong=(
            r"big data analytics certificate",
            r"certificate big data analytics",
            r"professional certificate big data analytics",
            r"big data analytics.*certificate",
            r"certificate.*big data analytics",
        ),
        medium=(r"big data analytics", r"big data", r"certificate", r"worksheet", r"application", r"cap\s*6315", r"cap\s*6780"),
        weak=(r"data mining", r"data analytics", r"data science"),
        require_any=(r"big data", r"cap\s*6315", r"cap\s*6780"),
    ),
    "q04": QueryRule(
        query_id="q04",
        strong=(
            r"ms in computer science",
            r"master.*computer science",
            r"ms computer science",
            r"ms cse worksheet",
            r"professional ms cs",
            r"computer science program worksheet",
            r"computer science.*program worksheet",
        ),
        medium=(r"computer science", r"\bms\b", r"graduate", r"program worksheet", r"worksheet", r"cse"),
        weak=(r"cop\s*\d{4}", r"cap\s*\d{4}", r"cot\s*\d{4}", r"cen\s*\d{4}"),
        require_any=(r"computer science", r"\bcse\b", r"\bcs\b"),
    ),
    "q05": QueryRule(
        query_id="q05",
        strong=(
            r"ms in computer engineering",
            r"master.*computer engineering",
            r"ms computer engineering",
            r"ms coen worksheet",
            r"computer engineering program sheet",
            r"computer engineering.*program",
            r"\bce application form\b",
        ),
        medium=(r"computer engineering", r"\bcoen\b", r"\bce\b", r"\bms\b", r"program sheet", r"worksheet", r"application form"),
        weak=(r"cda\s*\d{4}", r"cen\s*\d{4}", r"embedded systems", r"computer architecture"),
        require_any=(r"computer engineering", r"\bcoen\b", r"\bce application"),
    ),
    "q06": QueryRule(
        query_id="q06",
        strong=(
            r"ms in electrical engineering",
            r"master.*electrical engineering",
            r"ms electrical engineering",
            r"electrical engineering program sheet",
            r"electrical engineering.*worksheet",
            r"ms in eel worksheet",
            r"ms eel worksheet",
            r"ms to phd electrical engineering",
            r"bs to phd electrical engineering",
        ),
        medium=(r"electrical engineering", r"\beel\b", r"\beee\b", r"\bms\b", r"program sheet", r"worksheet", r"graduate"),
        weak=(r"signal processing", r"communications", r"control systems", r"power systems", r"smart grid", r"rf"),
        require_any=(r"electrical engineering", r"\beel\b", r"\beee\b"),
    ),
    "q07": QueryRule(
        query_id="q07",
        strong=(
            r"cybersecurity certificate",
            r"cyber security certificate",
            r"cybersecurity minor",
            r"cyber security minor",
            r"ms phd cybersecurity",
            r"cybersecurity concentration",
            r"cybersecurity.*worksheet",
            r"cyber security.*worksheet",
            r"certificate.*cyber security",
            r"certificate.*cybersecurity",
        ),
        medium=(
            r"cybersecurity",
            r"cyber security",
            r"cryptography",
            r"cryptographic",
            r"network security",
            r"data security",
            r"distributed systems security",
            r"security",
            r"worksheet",
            r"application",
            r"concentration",
        ),
        weak=(r"cis\s*6370", r"cis\s*6375", r"cnt\s*4403", r"cda\s*5326", r"cot\s*4930", r"cts\s*6319"),
        require_any=(r"cyber", r"security", r"cryptograph"),
    ),
    "q08": QueryRule(
        query_id="q08",
        strong=(
            r"data science certificate",
            r"data science analytics",
            r"data science and analytics",
            r"\bdsa\b.*worksheet",
            r"\bcsda\b.*worksheet",
            r"computer science data analytics",
            r"data science.*program worksheet",
            r"ms in data science analytics",
            r"ms phd.*data science",
            r"bs phd.*data science",
        ),
        medium=(r"data science", r"data analytics", r"\bdsa\b", r"\bcsda\b", r"certificate", r"worksheet", r"concentration", r"cap\s*5768"),
        weak=(r"data mining", r"machine learning", r"big data", r"database", r"analytics"),
        require_any=(r"data science", r"data analytics", r"\bdsa\b", r"\bcsda\b", r"cap\s*5768"),
    ),
    "q09": QueryRule(
        query_id="q09",
        strong=(
            r"applied machine learning",
            r"machine learning computer vision",
            r"deep learning",
            r"intro.*neural networks",
            r"natural language processing",
            r"computational foundations.*artificial intelligence",
            r"trustworthy artificial intelligence",
            r"conversational ai",
            r"generative ai",
            r"cap\s*6610",
            r"cap\s*6618",
            r"cap\s*6619",
            r"cap\s*5615",
            r"cap\s*6640",
            r"cap\s*5625",
        ),
        medium=(r"machine learning", r"artificial intelligence", r"neural", r"deep learning", r"computer vision", r"\bnlp\b", r"course syllabus", r"syllabus", r"\bcap\b"),
        weak=(r"data mining", r"big data", r"intelligent", r"autonomous robots"),
        require_any=(r"machine learning", r"artificial intelligence", r"neural", r"deep learning", r"computer vision", r"\bnlp\b", r"cap\s*661", r"cap\s*56", r"cap\s*66"),
    ),
    "q10": QueryRule(
        query_id="q10",
        strong=(
            r"intro data mining",
            r"data mining machine learning",
            r"information retrieval",
            r"web mining",
            r"advanced data mining",
            r"big data analytics",
            r"database structures",
            r"database systems",
            r"cap\s*4770",
            r"cap\s*6673",
            r"cap\s*6776",
            r"cap\s*6777",
            r"cap\s*6778",
            r"cap\s*6780",
            r"cop\s*3540",
            r"cop\s*4703",
            r"cop\s*6726",
            r"cop\s*6731",
        ),
        medium=(r"data mining", r"information retrieval", r"web mining", r"big data", r"database", r"analytics", r"course syllabus", r"syllabus"),
        weak=(r"machine learning", r"data science", r"semantic web", r"visual information retrieval"),
        require_any=(r"data mining", r"information retrieval", r"web mining", r"big data", r"database", r"cap\s*677", r"cop\s*67"),
    ),
    "q11": QueryRule(
        query_id="q11",
        strong=(
            r"principles.*software engineering",
            r"software engineering",
            r"software requirements engineering",
            r"software testing",
            r"software architecture",
            r"software maintenance",
            r"object oriented design",
            r"object oriented software design",
            r"cen\s*4010",
            r"cen\s*5035",
            r"cen\s*6075",
            r"cen\s*6076",
            r"cen\s*6085",
            r"cen\s*6027",
            r"cop\s*4331",
            r"cop\s*5339",
        ),
        medium=(r"software", r"requirements", r"testing", r"architecture", r"maintenance", r"object oriented", r"design", r"course syllabus", r"syllabus"),
        weak=(r"cloud computing", r"component programming", r"programming languages"),
        require_any=(r"software", r"object oriented", r"cen\s*40", r"cen\s*50", r"cen\s*60", r"cop\s*4331", r"cop\s*5339"),
    ),
    "q12": QueryRule(
        query_id="q12",
        strong=(
            r"circuits",
            r"electronics",
            r"signal processing",
            r"communications",
            r"communication systems",
            r"control systems",
            r"antenna",
            r"rf",
            r"microwave",
            r"power systems",
            r"smart grid",
            r"photovoltaic",
            r"\beel\s*\d{4}",
            r"\beee\s*\d{4}",
        ),
        medium=(r"electrical engineering", r"\beel\b", r"\beee\b", r"course syllabus", r"syllabus", r"graduate", r"undergraduate"),
        weak=(r"wireless", r"radar", r"fiber optic", r"electromagnetic", r"linear systems", r"lab"),
        require_any=(r"\beel\b", r"\beee\b", r"electrical engineering", r"circuits", r"electronics", r"signal processing", r"communications", r"control systems"),
        max_per_query=40,
    ),
    "q13": QueryRule(
        query_id="q13",
        strong=(
            r"digital logic",
            r"logic design",
            r"microprocessor",
            r"microcontrollers",
            r"computer architecture",
            r"structured computer architecture",
            r"embedded systems",
            r"vlsi",
            r"cad based computer design",
            r"computer design",
            r"\bcda\s*\d{4}",
        ),
        medium=(r"\bcda\b", r"architecture", r"embedded", r"digital", r"computer design", r"course syllabus", r"syllabus"),
        weak=(r"hardware", r"processor", r"parallel", r"distributed systems", r"computer systems"),
        require_any=(r"\bcda\b", r"digital logic", r"microprocessor", r"embedded", r"vlsi", r"computer architecture", r"computer design"),
    ),
    "q14": QueryRule(
        query_id="q14",
        strong=(
            r"audit form",
            r"application form",
            r"program application",
            r"graduate pathway scholarship",
            r"low residency phd",
            r"conflict of interest",
            r"disclosure",
            r"bsms audit",
            r"bsphd audit",
            r"phd form",
        ),
        medium=(r"form", r"application", r"audit", r"worksheet", r"scholarship", r"graduate pathway", r"student forms"),
        weak=(r"program worksheet", r"certificate", r"minor", r"department", r"eecs"),
        require_any=(r"form", r"application", r"audit", r"scholarship", r"conflict", r"low residency", r"worksheet"),
        max_per_query=40,
    ),
}


# Narrow query families after definition:
# - Form/program queries should not be dominated by generic course-listing rows.
# - Course-syllabus queries should not be dominated by program worksheets that merely list courses.
FORM_FOCUSED_QIDS = ("q01", "q02", "q03", "q04", "q05", "q06", "q14")
FORM_FOCUSED_EXCLUDES = (r"document type\s*=?\s*course listing",)

COURSE_FOCUSED_QIDS = ("q09", "q10", "q11", "q12", "q13")
COURSE_FOCUSED_EXCLUDES = (
    r"document type\s*=?\s*program form or worksheet",
    r"program form or worksheet",
    r"certificate",
    r"minor",
    r"application",
    r"worksheet",
)

for _qid in FORM_FOCUSED_QIDS:
    _rule = QUERY_RULES[_qid]
    QUERY_RULES[_qid] = replace(_rule, exclude=_rule.exclude + FORM_FOCUSED_EXCLUDES)

for _qid in COURSE_FOCUSED_QIDS:
    _rule = QUERY_RULES[_qid]
    QUERY_RULES[_qid] = replace(_rule, exclude=_rule.exclude + COURSE_FOCUSED_EXCLUDES)


def make_search_blob(row: pd.Series) -> str:
    """
    Join metadata plus a short text preview for rule matching.

    Using the full extracted PDF text can over-label program worksheets because
    those PDFs often contain long course lists. Metadata and the start of the
    labeled text usually contain the document title, course code, filename, and
    document type, which are better signals for qrels.
    """
    metadata_cols = [
        "doc_id",
        "document_type",
        "title",
        "course_code",
        "prefix",
        "number",
        "level",
        "source_page",
        "linked_file_or_page",
        "file_name",
    ]
    pieces = []
    for col in metadata_cols:
        if col in row.index:
            pieces.append(str(row[col]))

    # Add only a preview of the labeled text to capture missing metadata without
    # letting long course requirement lists dominate relevance decisions.
    if "text" in row.index:
        pieces.append(str(row["text"])[:1500])

    return norm(" | ".join(pieces))


def score_document(rule: QueryRule, blob: str) -> tuple[int, int, str]:
    """
    Returns:
        relevance, raw_score, reason
    """
    if any(regex_hit(pattern, blob) for pattern in rule.exclude):
        return 0, 0, "excluded"

    if rule.require_any and not any(regex_hit(pattern, blob) for pattern in rule.require_any):
        return 0, 0, "missing_required_anchor"

    strong_hits = count_hits(rule.strong, blob)
    medium_hits = count_hits(rule.medium, blob)
    weak_hits = count_hits(rule.weak, blob)

    raw_score = (strong_hits * 5) + (medium_hits * 2) + weak_hits

    if raw_score >= 8 or strong_hits >= 2:
        relevance = 2
    elif raw_score >= 4 or strong_hits >= 1:
        relevance = 1
    else:
        relevance = 0

    reason = f"strong={strong_hits}; medium={medium_hits}; weak={weak_hits}; score={raw_score}"
    return relevance, raw_score, reason


def build_qrels(
    corpus_path: Path,
    queries_path: Path,
    output_path: Path,
    review_output_path: Path | None = Path("search_review/eecs_qrels_review.csv"),
    default_max_per_query: int = 30,
) -> pd.DataFrame:
    if not corpus_path.exists():
        raise FileNotFoundError(
            f"Could not find {corpus_path}. Build the EECS corpus first, then run this script."
        )
    if not queries_path.exists():
        raise FileNotFoundError(
            f"Could not find {queries_path}. Run build_eecs_queries.py first."
        )

    corpus_df = pd.read_csv(corpus_path).fillna("")
    queries_df = pd.read_csv(queries_path).fillna("")

    required_corpus_cols = {"doc_id", "text"}
    missing_corpus = required_corpus_cols - set(corpus_df.columns)
    if missing_corpus:
        raise ValueError(f"corpus.csv is missing required columns: {sorted(missing_corpus)}")

    required_query_cols = {"query_id", "query_text"}
    missing_queries = required_query_cols - set(queries_df.columns)
    if missing_queries:
        raise ValueError(f"queries.csv is missing required columns: {sorted(missing_queries)}")

    # Friendly warning if someone accidentally points this at the old healthcare corpus.
    sample_text = norm(" ".join(corpus_df["text"].head(10).astype(str).tolist()))
    if "condition = heart disease" in sample_text or "length of stay" in sample_text or "epinephrine injection" in sample_text:
        print("WARNING: This looks like the old healthcare corpus, not the EECS corpus.")
        print("         Rebuild data/corpus.csv from DepCourseInfo before using these qrels.")

    blobs = {}
    row_lookup = {}
    for _, row in corpus_df.iterrows():
        doc_id = str(row["doc_id"])
        blobs[doc_id] = make_search_blob(row)
        row_lookup[doc_id] = row

    qrel_rows = []
    review_rows = []

    for qrow in queries_df.itertuples(index=False):
        qid = str(qrow.query_id)
        qtext = str(qrow.query_text)
        rule = QUERY_RULES.get(qid)

        if rule is None:
            print(f"WARNING: No rule found for {qid}; skipping qrels for this query.")
            continue

        candidates = []
        for doc_id, blob in blobs.items():
            relevance, score, reason = score_document(rule, blob)
            if relevance > 0:
                candidates.append((doc_id, relevance, score, reason))

        # Sort: strong labels first, then higher score, then stable doc_id.
        candidates.sort(key=lambda item: (-item[1], -item[2], item[0]))

        limit = rule.max_per_query or default_max_per_query
        if limit is None or limit <= 0:
            limited = candidates
        else:
            limited = candidates[:limit]

        for doc_id, relevance, score, reason in limited:
            qrel_rows.append({
                "query_id": qid,
                "doc_id": doc_id,
                "relevance": int(relevance),
            })

            row_obj = row_lookup[doc_id]
            row_dict = row_obj.to_dict() if hasattr(row_obj, "to_dict") else dict(row_obj)
            text = str(row_dict.get("text", ""))
            review_rows.append({
                "query_id": qid,
                "query_text": qtext,
                "doc_id": doc_id,
                "relevance": int(relevance),
                "score": int(score),
                "reason": reason,
                "document_type": row_dict.get("document_type", ""),
                "title": row_dict.get("title", ""),
                "course_code": row_dict.get("course_code", ""),
                "file_name": row_dict.get("file_name", ""),
                "preview": re.sub(r"\s+", " ", text)[:400],
            })

    qrels_df = pd.DataFrame(qrel_rows, columns=["query_id", "doc_id", "relevance"])
    review_df = pd.DataFrame(review_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    qrels_df.to_csv(output_path, index=False)

    print(f"Saved {len(qrels_df)} qrel rows to: {output_path}")
    if len(qrels_df) > 0:
        print("\nRelevance counts by query:")
        print(qrels_df.groupby(["query_id", "relevance"]).size().unstack(fill_value=0).to_string())

    if review_output_path is not None:
        review_output_path.parent.mkdir(parents=True, exist_ok=True)
        review_df.to_csv(review_output_path, index=False)
        print(f"\nSaved review file to: {review_output_path}")
        print("Open this review CSV to manually approve/edit weak labels before final evaluation.")

    missing_qids = sorted(set(queries_df["query_id"].astype(str)) - set(qrels_df["query_id"].astype(str)))
    if missing_qids:
        print(f"\nWARNING: No qrels were generated for: {missing_qids}")

    return qrels_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Create weakly supervised EECS qrels.csv.")
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus.csv"), help="Input corpus CSV.")
    parser.add_argument("--queries", type=Path, default=Path("search_review/eecs_queries.csv"), help="Input queries CSV.")
    parser.add_argument("--output", type=Path, default=Path("search_review/eecs_qrels.csv"), help="Output qrels CSV.")
    parser.add_argument(
        "--review-output",
        type=Path,
        default=Path("search_review/eecs_qrels_review.csv"),
        help="Optional review CSV with reasons and previews. Use 'none' to skip.",
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=30,
        help="Fallback maximum qrel rows per query when a rule does not override it.",
    )
    args = parser.parse_args()

    review_output = None if str(args.review_output).lower() == "none" else args.review_output

    build_qrels(
        corpus_path=args.corpus,
        queries_path=args.queries,
        output_path=args.output,
        review_output_path=review_output,
        default_max_per_query=args.max_per_query,
    )


if __name__ == "__main__":
    main()
