# EECS Retrieval Evaluation CSV Workflow

This version keeps the three starter evaluation CSVs in a separate folder named `search_review/`.

## Folder layout

```text
project_folder/
├── data/
│   └── corpus.csv
├── search_review/
│   ├── eecs_queries.csv
│   ├── eecs_qrels.csv
│   └── eecs_qrels_review.csv
├── build_eecs_eval_files.py
├── build_eecs_queries.py
├── build_eecs_qrels.py
└── validate_eecs_eval_files.py
```

## What each CSV does

| File | Purpose |
|---|---|
| `search_review/eecs_queries.csv` | Starter EECS retrieval questions. Uses `query_id, query_text`. |
| `search_review/eecs_qrels.csv` | Template-compatible relevance labels. Uses `query_id, doc_id, relevance`. |
| `search_review/eecs_qrels_review.csv` | Human-review file with reasons, scores, titles, filenames, and previews. |

## Build all three files

Run this after `data/corpus.csv` exists:

```bash
python build_eecs_eval_files.py
```

This writes:

```text
search_review/eecs_queries.csv
search_review/eecs_qrels.csv
search_review/eecs_qrels_review.csv
```

## Validate the files

```bash
python validate_eecs_eval_files.py
```

The validator checks that:

- `data/corpus.csv` has `doc_id` and `text`
- `search_review/eecs_queries.csv` has `query_id` and `query_text`
- `search_review/eecs_qrels.csv` has `query_id`, `doc_id`, and `relevance`
- every qrel query exists in the queries file
- every qrel document exists in the corpus
- relevance labels are limited to `0`, `1`, or `2`

## Older notebook compatibility

If you are using an older notebook that still expects `data/queries.csv` and `data/qrels.csv`, run:

```bash
python build_eecs_eval_files.py --sync-template-data
```

That keeps the reviewed starter files in `search_review/` and also writes compatibility copies to:

```text
data/queries.csv
data/qrels.csv
```

## Recommended workflow

1. Build or refresh `data/corpus.csv` from the department files.
2. Run `python build_eecs_eval_files.py`.
3. Open `search_review/eecs_qrels_review.csv` and manually inspect the labels.
4. Edit `search_review/eecs_qrels.csv` if you want final hand-reviewed relevance labels.
5. Run `python validate_eecs_eval_files.py`.
6. Run the retrieval notebook evaluation cells.
