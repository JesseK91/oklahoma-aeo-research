#!/usr/bin/env python3
"""Reproduce the descriptive statistics in Research Report 003.

This script uses only the Python standard library. It does not modify the
source exports. Results are written as JSON so the calculations can be
reviewed independently or used to build publication tables and figures.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


TOP_N = (1, 3, 5, 10, 20, 50, 100, 250, 500, 1000)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def percentile(values: list[float], fraction: float) -> float:
    """Return a linearly interpolated percentile using the (n - 1) index."""

    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def average_ranks(values: list[float]) -> list[float]:
    """Return one-based average ranks, preserving ties."""

    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start
        while end + 1 < len(ordered) and ordered[end + 1][1] == ordered[start][1]:
            end += 1
        average = ((start + 1) + (end + 1)) / 2
        for position in range(start, end + 1):
            ranks[ordered[position][0]] = average
        start = end + 1
    return ranks


def pearson(left: list[float], right: list[float]) -> float:
    left_mean = statistics.mean(left)
    right_mean = statistics.mean(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    denominator = math.sqrt(
        sum((x - left_mean) ** 2 for x in left) * sum((y - right_mean) ** 2 for y in right)
    )
    return numerator / denominator


def concentration(values: list[int]) -> dict[str, dict[str, float | int]]:
    ordered = sorted(values, reverse=True)
    total = sum(ordered)
    return {
        f"top_{limit}": {
            "citations": sum(ordered[:limit]),
            "percent": round(sum(ordered[:limit]) / total * 100, 4),
        }
        for limit in TOP_N
        if limit <= len(ordered)
    }


def rolling_mean(values: list[int], window: int) -> list[float]:
    return [statistics.mean(values[index - window + 1 : index + 1]) for index in range(window - 1, len(values))]


def overview_analysis(rows: list[dict[str, str]]) -> dict[str, object]:
    dates = [datetime.strptime(row["Date"], "%m/%d/%Y %I:%M:%S %p").date() for row in rows]
    citations = [int(row["Citations"]) for row in rows]
    cited_pages = [int(row["Cited Pages"]) for row in rows]
    unique_dates = set(dates)
    expected_dates = {
        dates[0] + timedelta(days=offset) for offset in range((dates[-1] - dates[0]).days + 1)
    }
    seven_day = rolling_mean(citations, 7)
    seven_day_pages = rolling_mean(cited_pages, 7)
    seven_day_end_dates = dates[6:]
    peak_index = max(range(len(seven_day)), key=seven_day.__getitem__)
    minimum_index = min(range(len(seven_day)), key=seven_day.__getitem__)
    first_30_citations = statistics.mean(citations[:30])
    final_30_citations = statistics.mean(citations[-30:])
    first_30_pages = statistics.mean(cited_pages[:30])
    final_30_pages = statistics.mean(cited_pages[-30:])

    monthly: dict[str, dict[str, float | int]] = {}
    for date, citation_count, page_count in zip(dates, citations, cited_pages):
        key = date.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = {"days": 0, "citations": 0, "cited_pages_sum": 0}
        monthly[key]["days"] += 1
        monthly[key]["citations"] += citation_count
        monthly[key]["cited_pages_sum"] += page_count
    for values in monthly.values():
        values["daily_citation_mean"] = values["citations"] / values["days"]
        values["daily_cited_pages_mean"] = values.pop("cited_pages_sum") / values["days"]

    return {
        "rows": len(rows),
        "start_date": dates[0].isoformat(),
        "end_date": dates[-1].isoformat(),
        "inclusive_days": (dates[-1] - dates[0]).days + 1,
        "unique_dates": len(unique_dates),
        "missing_dates": sorted(date.isoformat() for date in expected_dates - unique_dates),
        "duplicate_date_rows": len(dates) - len(unique_dates),
        "citations": {
            "total": sum(citations),
            "daily_mean": statistics.mean(citations),
            "daily_median": statistics.median(citations),
            "daily_standard_deviation": statistics.stdev(citations),
            "minimum": min(citations),
            "minimum_date": dates[citations.index(min(citations))].isoformat(),
            "maximum": max(citations),
            "maximum_date": dates[citations.index(max(citations))].isoformat(),
        },
        "cited_pages": {
            "daily_mean": statistics.mean(cited_pages),
            "daily_median": statistics.median(cited_pages),
            "daily_standard_deviation": statistics.stdev(cited_pages),
            "minimum": min(cited_pages),
            "minimum_date": dates[cited_pages.index(min(cited_pages))].isoformat(),
            "maximum": max(cited_pages),
            "maximum_date": dates[cited_pages.index(max(cited_pages))].isoformat(),
        },
        "daily_citations_cited_pages_pearson": pearson(
            [float(value) for value in citations], [float(value) for value in cited_pages]
        ),
        "seven_day_rolling_citations": {
            "first": seven_day[0],
            "first_end_date": seven_day_end_dates[0].isoformat(),
            "peak": seven_day[peak_index],
            "peak_end_date": seven_day_end_dates[peak_index].isoformat(),
            "minimum": seven_day[minimum_index],
            "minimum_end_date": seven_day_end_dates[minimum_index].isoformat(),
            "final": seven_day[-1],
            "final_end_date": seven_day_end_dates[-1].isoformat(),
        },
        "seven_day_rolling_cited_pages": {
            "first": seven_day_pages[0],
            "final": seven_day_pages[-1],
        },
        "first_vs_final_30_days": {
            "first_daily_citation_mean": first_30_citations,
            "final_daily_citation_mean": final_30_citations,
            "citation_mean_change_percent": (final_30_citations / first_30_citations - 1) * 100,
            "first_daily_cited_pages_mean": first_30_pages,
            "final_daily_cited_pages_mean": final_30_pages,
            "cited_pages_mean_change_percent": (final_30_pages / first_30_pages - 1) * 100,
        },
        "monthly": monthly,
    }


def query_analysis(rows: list[dict[str, str]]) -> dict[str, object]:
    citations = [int(row["Citations"]) for row in rows]
    shares = [float(row["Citation Share"].rstrip("%")) for row in rows]

    intent_citations: Counter[str] = Counter()
    for row in rows:
        intent_citations[row["Intent"].strip() or "Unclassified"] += int(row["Citations"])

    family_patterns = {
        "Hawas Ice": re.compile(r"hawas ice", re.I),
        "Imagination": re.compile(r"imagination", re.I),
        "God of Fire": re.compile(r"god of fire", re.I),
        "Afnan 9PM": re.compile(r"afnan 9\s*pm", re.I),
        "Rayhaan Obsidian": re.compile(r"rayhaan obsidian", re.I),
        "Khamrah": re.compile(r"khamrah", re.I),
    }
    families: dict[str, dict[str, int]] = {}
    for name, pattern in family_patterns.items():
        matching = [row for row in rows if pattern.search(row["Grounding Query"])]
        families[name] = {
            "groups": len(matching),
            "citations": sum(int(row["Citations"]) for row in matching),
        }

    return {
        "rows": len(rows),
        "citations": sum(citations),
        "concentration": concentration(citations),
        "intent_citations": dict(intent_citations.most_common()),
        "citation_share": {
            "minimum": min(shares),
            "first_quartile": percentile(shares, 0.25),
            "median": statistics.median(shares),
            "third_quartile": percentile(shares, 0.75),
            "maximum": max(shares),
        },
        "correlation": {
            "pearson": pearson([float(value) for value in citations], shares),
            "spearman": pearson(average_ranks([float(value) for value in citations]), average_ranks(shares)),
        },
        "concept_families": families,
    }


def page_analysis(rows: list[dict[str, str]]) -> dict[str, object]:
    citations = [int(row["Citations"]) for row in rows]
    family_pages: Counter[str] = Counter()
    family_citations: Counter[str] = Counter()

    for row in rows:
        path = urlparse(row["Page"]).path.strip("/")
        family = path.split("/")[0] if path else "homepage"
        family_pages[family] += 1
        family_citations[family] += int(row["Citations"])

    structured = ("fragrance", "clone", "clone-of")
    structured_pages = sum(family_pages[family] for family in structured)
    structured_citations = sum(family_citations[family] for family in structured)

    return {
        "rows": len(rows),
        "citations": sum(citations),
        "mean_citations": statistics.mean(citations),
        "median_citations": statistics.median(citations),
        "concentration": concentration(citations),
        "url_families": {
            family: {
                "pages": family_pages[family],
                "citations": count,
                "percent": round(count / sum(citations) * 100, 4),
            }
            for family, count in family_citations.most_common()
        },
        "structured_entity_relationship_pages": {
            "families": list(structured),
            "pages": structured_pages,
            "citations": structured_citations,
            "percent": round(structured_citations / sum(citations) * 100, 4),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("overview_csv", type=Path)
    parser.add_argument("query_csv", type=Path)
    parser.add_argument("page_csv", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = {
        "overview": overview_analysis(read_csv(args.overview_csv)),
        "grounding_queries": query_analysis(read_csv(args.query_csv)),
        "pages": page_analysis(read_csv(args.page_csv)),
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
