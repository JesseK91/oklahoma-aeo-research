# The 2026 Oklahoma Local AI Shortlist Study (Report 004)

1,080 saved Gemini API responses, 540 paired wording comparisons, fifteen Oklahoma
cities, and twelve service categories. Read `REPORT-004.md` for the main findings and
`TECHNICAL-APPENDIX.md` for the methods, statistical tables, and study limits.

## Reproduce the results

Requires Python 3.10 or newer using only the standard library. No API keys or network
requests are used during reproduction:

```
python3 study_analyzer.py --input-dir . --output-dir derived
python3 generate_figures.py --data-dir derived --output-dir derived/figures
python3 verify_reproducibility.py
sha256sum -c SHA256SUMS.txt
```

The verification script checks specific response extraction cases, confirms every table
denominator, and runs three full offline analysis and figure replays under different
Python hash seeds. Identical output bytes are expected within the same Python
environment.

## Files and definitions

- `raw_1080_runs.json`: exact saved prompts, response texts, source title and URI lists,
  and recorded search query strings from the collection archive. Derived fields are
  omitted. These are saved observation records rather than full raw API envelopes.
- `inspection_snapshot.csv`: frozen homepage observations for 1,667 candidate domains.
  Not every domain is an independently verified local business. Original city and
  category assignments, title and H1 records, city text flags, and recorded schema types
  are retained.
- `study_config.json`: collection configuration and seed sites. The file documents the
  prompts and seed domains used in the run, not an independently timestamped
  preregistration.
- `manual_name_overrides.json`: source-checked transcriptions for the ten unformatted
  answers and one mixed-format answer, listed in order of appearance.
- `extracted_names.csv`: every extracted provider name, its list position, and its
  normalized identity.
- `paraphrase_pairs_540.csv`: all 540 paired question comparisons with extracted name
  lists, Jaccard overlap, and first name agreement.
- `domain_name_matches.csv`: accepted, ambiguous, and unmatched domain to name linking
  decisions.
- `grounding_sources.csv`: all 8,370 saved grounding source entries and their explicit
  source classifications.
- `businesses_inspected.csv`: homepage inspection records paired with conservative name
  match groups.
- `study_summary.json`: statewide totals, city and category breakdowns, five exploratory
  homepage comparisons, Holm adjustments, and a 2,000-draw primary cell bootstrap using
  fixed seed 40021.

In the CSV exports, compatibility column names starting with `top_1_*` refer to the
first extracted name in the response, not an explicit ranking endorsement. The columns
`runs_shortlisted_in` and `inslr_percent` in the website table count conservative name
matches out of the six prompts in the domain's primary city and category cell. The column
`has_schema` is an alias for `has_parseable_schema_type`; neither certifies full
Schema.org validity. For backward compatibility with earlier links, `runs_90_summary.csv`
and `paraphrase_pairs_45.csv` are retained as file aliases for the full 1,080 and 540
row tables.

## Interpretation notes

Extracted names can include individual insurance agents, national brands, directories,
and off-category suggestions. Normalization preserves city and service words inside
names, which can keep branch or spelling variations separate. Having no matched name in
the website table does not prove a business was absent from the answers. Paired question
differences reflect both prompt wording and ordinary model and search retrieval
variation, as the dataset does not include repeated identical prompts. Customer calls,
leads, and revenue were not measured.

Full raw API envelopes, passage-level grounding support mappings, individual execution
timestamps, raw crawled HTML files, and verified business ownership records for all
source domains are not part of this archive.

## Optional live collection scripts

The live collection scripts (`study_runner.py` and `benchmarker.py`) require the
`requests` package and an explicit `GEMINI_API_KEY` environment variable. They write to
`fresh-observations/` by default and are never called during offline reproduction.
Running a fresh collection queries a live search index and current model state, which
will differ from the frozen October 2026 observations.

## Rights

Original report prose, tables, and figures are licensed under CC BY 4.0 by Jesse Killian
and 580 Digital Infrastructure. Original analysis scripts are released under the MIT
License. Third-party website titles, names, and URLs remain subject to their respective
owners' rights. File checksums verify archive integrity and do not certify the factual
accuracy of third-party statements inside generated AI responses.
