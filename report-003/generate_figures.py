#!/usr/bin/env python3
"""Generate publication SVG figures for Research Report 003."""

from __future__ import annotations

import argparse
import csv
import html
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


PAPER = "#f3ead8"
SURFACE = "#fff9ed"
INK = "#11100e"
MUTED = "#655d51"
ORANGE = "#f05a24"
LINE = "#c7baa4"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def svg_document(title: str, description: str, body: str, width: int = 1200, height: int = 760) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{html.escape(title)}</title>
  <desc id="desc">{html.escape(description)}</desc>
  <rect width="{width}" height="{height}" fill="{PAPER}"/>
  <style>
    text {{ font-family: "Libre Franklin", Arial, sans-serif; fill: {INK}; }}
    .label {{ font-size: 15px; font-weight: 750; letter-spacing: 1.4px; text-transform: uppercase; fill: {ORANGE}; }}
    .title {{ font-size: 45px; font-weight: 820; letter-spacing: -2.2px; }}
    .note {{ font-size: 16px; fill: {MUTED}; }}
    .axis {{ font-size: 14px; fill: {MUTED}; }}
    .value {{ font-size: 17px; font-weight: 760; }}
  </style>
  {body}
</svg>
'''


def rolling_mean(values: list[int], window: int) -> list[float]:
    return [sum(values[index - window + 1 : index + 1]) / window for index in range(window - 1, len(values))]


def time_series_figure(rows: list[dict[str, str]]) -> str:
    dates = [datetime.strptime(row["Date"], "%m/%d/%Y %I:%M:%S %p") for row in rows]
    citations = [int(row["Citations"]) for row in rows]
    cited_pages = [int(row["Cited Pages"]) for row in rows]
    rolling_citations = rolling_mean(citations, 7)
    rolling_pages = rolling_mean(cited_pages, 7)
    rolling_dates = dates[6:]
    left, right, top, bottom = 105, 1095, 205, 625
    citation_max, pages_max = 600, 160
    span = (dates[-1] - dates[0]).total_seconds()

    def sx(date: datetime) -> float:
        return left + (date - dates[0]).total_seconds() / span * (right - left)

    def citation_y(value: float) -> float:
        return bottom - value / citation_max * (bottom - top)

    def pages_y(value: float) -> float:
        return bottom - value / pages_max * (bottom - top)

    def points(series_dates: list[datetime], values: list[float], y_scale) -> str:
        return " ".join(f"{sx(date):.1f},{y_scale(value):.1f}" for date, value in zip(series_dates, values))

    parts = [
        '<text class="label" x="70" y="62">Figure 1 / Time</text>',
        '<text class="title" x="70" y="116">The six-month total was not a steady state.</text>',
        '<text class="note" x="70" y="150">181 consecutive days · February 11 to August 10, 2026 · no missing dates</text>',
    ]

    for tick in range(0, citation_max + 1, 100):
        y = citation_y(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="{LINE}"/>')
        parts.append(f'<text class="axis" x="{left - 14}" y="{y + 5:.1f}" text-anchor="end">{tick}</text>')

    for tick in range(0, pages_max + 1, 40):
        y = pages_y(tick)
        parts.append(f'<text class="axis" x="{right + 14}" y="{y + 5:.1f}">{tick}</text>')

    month_ticks: list[datetime] = []
    for date in dates:
        if date.day == 1:
            month_ticks.append(date)
    for date in month_ticks:
        x = sx(date)
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="{LINE}" stroke-dasharray="3 7"/>')
        parts.append(f'<text class="axis" x="{x:.1f}" y="{bottom + 30}" text-anchor="middle">{date.strftime("%b")}</text>')

    parts.extend(
        [
            f'<text class="axis" x="24" y="{(top + bottom) / 2}" transform="rotate(-90 24 {(top + bottom) / 2})" text-anchor="middle">Daily citations</text>',
            f'<text class="axis" x="1173" y="{(top + bottom) / 2}" transform="rotate(90 1173 {(top + bottom) / 2})" text-anchor="middle">Daily cited pages</text>',
            f'<polyline points="{points(dates, [float(value) for value in citations], citation_y)}" fill="none" stroke="{ORANGE}" stroke-opacity="0.22" stroke-width="1.5"/>',
            f'<polyline points="{points(rolling_dates, rolling_citations, citation_y)}" fill="none" stroke="{ORANGE}" stroke-width="5"/>',
            f'<polyline points="{points(rolling_dates, rolling_pages, pages_y)}" fill="none" stroke="{INK}" stroke-width="3" stroke-dasharray="10 7"/>',
            f'<line x1="70" y1="704" x2="108" y2="704" stroke="{ORANGE}" stroke-width="5"/>',
            '<text class="axis" x="120" y="709">7-day average citations</text>',
            f'<line x1="340" y1="704" x2="378" y2="704" stroke="{INK}" stroke-width="3" stroke-dasharray="10 7"/>',
            '<text class="axis" x="390" y="709">7-day average cited pages</text>',
            '<text class="note" x="1128" y="709" text-anchor="end">35,310 citations · 59.75 mean cited pages/day</text>',
            '<text class="axis" x="70" y="742">Daily citation mean: 195.1 · median: 178 · peak 7-day average: 401.7 ending July 26</text>',
        ]
    )
    return svg_document(
        "Daily citation and cited-page activity",
        "Time series of 181 days showing daily citation volatility and seven-day rolling averages for citations and cited pages.",
        "\n  ".join(parts),
    )


def scatter_figure(rows: list[dict[str, str]]) -> str:
    width, height = 1200, 760
    left, right, top, bottom = 110, 1120, 185, 650
    max_x, max_y = 180, 70

    def sx(value: float) -> float:
        return left + value / max_x * (right - left)

    def sy(value: float) -> float:
        return bottom - value / max_y * (bottom - top)

    parts = [
        '<text class="label" x="70" y="62">Figure 2 / Relative presence</text>',
        '<text class="title" x="70" y="116">Citation volume and Citation Share diverged.</text>',
        '<text class="note" x="70" y="150">Each point is one exported grounding-query group. N = 72.</text>',
    ]

    for tick in range(0, 71, 10):
        y = sy(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="{LINE}" stroke-width="1"/>')
        parts.append(f'<text class="axis" x="{left - 16}" y="{y + 5:.1f}" text-anchor="end">{tick}%</text>')

    for tick in range(0, 181, 30):
        x = sx(tick)
        parts.append(f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom + 8}" stroke="{INK}"/>')
        parts.append(f'<text class="axis" x="{x:.1f}" y="{bottom + 30}" text-anchor="middle">{tick}</text>')

    parts.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="{INK}" stroke-width="2"/>',
            f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{INK}" stroke-width="2"/>',
            f'<text class="axis" x="{(left + right) / 2}" y="704" text-anchor="middle">Citations represented in the grounding-query export</text>',
            f'<text class="axis" transform="translate(27 {(top + bottom) / 2}) rotate(-90)" text-anchor="middle">Citation Share</text>',
        ]
    )

    for row in rows:
        citations = float(row["Citations"])
        share = float(row["Citation Share"].rstrip("%"))
        radius = 5.5 if citations < 80 else 8
        parts.append(
            f'<circle cx="{sx(citations):.1f}" cy="{sy(share):.1f}" r="{radius}" fill="{ORANGE}" fill-opacity="0.64" stroke="{INK}" stroke-width="1"/>'
        )

    annotations = {
        "imagination dupe": (-12, -26, "173 citations / 14.08%"),
        "zara tobacco rich warm addictive": (-8, 45, "166 / 37.30%"),
        "hawas ice dupe of": (12, -42, "106 / 43.62%"),
        "varakh silver dupe": (15, -18, "10 / 66.67%"),
    }
    for row in rows:
        query = row["Grounding Query"]
        if query not in annotations:
            continue
        dx, dy, label = annotations[query]
        x = sx(float(row["Citations"]))
        y = sy(float(row["Citation Share"].rstrip("%")))
        anchor = "end" if dx < 0 else "start"
        parts.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + dx:.1f}" y2="{y + dy + 5:.1f}" stroke="{INK}"/>')
        parts.append(f'<text class="value" x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}">{html.escape(query)}</text>')
        parts.append(f'<text class="axis" x="{x + dx:.1f}" y="{y + dy + 19:.1f}" text-anchor="{anchor}">{label}</text>')

    parts.append('<text class="note" x="70" y="742">Pearson r = 0.028 · Spearman ρ = 0.181 · Descriptive association within a sampled export</text>')
    return svg_document(
        "Citation Count versus Citation Share",
        "Scatterplot of 72 grounding-query groups showing weak association between citation count and Citation Share.",
        "\n  ".join(parts),
        width,
        height,
    )


def concentration_figure(query_rows: list[dict[str, str]], page_rows: list[dict[str, str]]) -> str:
    query_values = sorted((int(row["Citations"]) for row in query_rows), reverse=True)
    page_values = sorted((int(row["Citations"]) for row in page_rows), reverse=True)
    query_total = sum(query_values)
    page_total = sum(page_values)
    limits = (1, 3, 5, 10, 20)
    query_percent = [sum(query_values[:limit]) / query_total * 100 for limit in limits]
    page_percent = [sum(page_values[:limit]) / page_total * 100 for limit in limits]

    left, chart_top, chart_bottom, max_width = 220, 205, 645, 850
    group_height = (chart_bottom - chart_top) / len(limits)
    parts = [
        '<text class="label" x="70" y="62">Figure 3 / Concentration</text>',
        '<text class="title" x="70" y="116">One property. Two different distribution shapes.</text>',
        '<text class="note" x="70" y="150">Percent of citations represented in each separate sampled export.</text>',
    ]

    for index, limit in enumerate(limits):
        y = chart_top + index * group_height
        qp = query_percent[index]
        pp = page_percent[index]
        parts.append(f'<text class="value" x="{left - 24}" y="{y + 25:.1f}" text-anchor="end">Top {limit}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{qp / 80 * max_width:.1f}" height="28" fill="{ORANGE}"/>')
        parts.append(f'<text class="value" x="{left + qp / 80 * max_width + 12:.1f}" y="{y + 21:.1f}">{qp:.1f}%</text>')
        parts.append(f'<rect x="{left}" y="{y + 38}" width="{pp / 80 * max_width:.1f}" height="20" fill="{INK}" fill-opacity="0.78"/>')
        parts.append(f'<text class="axis" x="{left + pp / 80 * max_width + 12:.1f}" y="{y + 54:.1f}">{pp:.1f}%</text>')

    parts.extend(
        [
            '<rect x="70" y="697" width="18" height="18" fill="#f05a24"/>',
            '<text class="axis" x="99" y="712">Grounding-query export</text>',
            '<rect x="310" y="697" width="18" height="18" fill="#11100e" fill-opacity="0.78"/>',
            '<text class="axis" x="339" y="712">Page export</text>',
            '<text class="note" x="1128" y="712" text-anchor="end">Separate views; not a joined denominator</text>',
        ]
    )
    return svg_document(
        "Grounding-query and page concentration",
        "Comparison showing that the top ten grounding queries held 55.1 percent of query-export citations while the top ten pages held 14.7 percent of page-export citations.",
        "\n  ".join(parts),
    )


def page_family_figure(page_rows: list[dict[str, str]]) -> str:
    families: dict[str, int] = {}
    for row in page_rows:
        path = urlparse(row["Page"]).path.strip("/")
        family = path.split("/")[0] if path else "homepage"
        families[family] = families.get(family, 0) + int(row["Citations"])

    ordered = [
        ("/fragrance", families["fragrance"]),
        ("/clone", families["clone"]),
        ("/clone-of", families["clone-of"]),
        ("/blog", families["blog"]),
        ("Other", sum(value for key, value in families.items() if key not in {"fragrance", "clone", "clone-of", "blog"})),
    ]
    total = sum(families.values())
    max_value = max(value for _, value in ordered)
    left, top, bar_width = 245, 215, 800
    parts = [
        '<text class="label" x="70" y="62">Figure 4 / Page architecture</text>',
        '<text class="title" x="70" y="116">Structured pages carried the citation activity.</text>',
        '<text class="note" x="70" y="150">Researcher-defined URL families within the 22,745-citation page export.</text>',
    ]

    for index, (family, value) in enumerate(ordered):
        y = top + index * 82
        percent = value / total * 100
        color = ORANGE if family in {"/fragrance", "/clone", "/clone-of"} else INK
        opacity = "1" if color == ORANGE else "0.76"
        width = value / max_value * bar_width
        parts.append(f'<text class="value" x="{left - 24}" y="{y + 28}" text-anchor="end">{family}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{width:.1f}" height="38" fill="{color}" fill-opacity="{opacity}"/>')
        parts.append(f'<text class="value" x="{left + width + 14:.1f}" y="{y + 27}">{value:,} · {percent:.1f}%</text>')

    parts.append('<line x1="70" y1="655" x2="1130" y2="655" stroke="#c7baa4"/>')
    parts.append('<text class="value" x="70" y="700">94.4%</text>')
    parts.append('<text class="note" x="151" y="700">of page-export citations came from /fragrance, /clone, and /clone-of pages.</text>')
    return svg_document(
        "Citation activity by URL family",
        "Horizontal bars showing 94.4 percent of page-export citations came from structured fragrance, clone, and clone-of pages.",
        "\n  ".join(parts),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("overview_csv", type=Path)
    parser.add_argument("query_csv", type=Path)
    parser.add_argument("page_csv", type=Path)
    parser.add_argument("output_directory", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    overview_rows = read_csv(args.overview_csv)
    query_rows = read_csv(args.query_csv)
    page_rows = read_csv(args.page_csv)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    figures = {
        "daily-ai-citation-activity.svg": time_series_figure(overview_rows),
        "citation-count-vs-share.svg": scatter_figure(query_rows),
        "query-page-concentration.svg": concentration_figure(query_rows, page_rows),
        "page-family-citations.svg": page_family_figure(page_rows),
    }
    for filename, contents in figures.items():
        (args.output_directory / filename).write_text(contents, encoding="utf-8")


if __name__ == "__main__":
    main()
