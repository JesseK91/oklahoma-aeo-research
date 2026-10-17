# 580 Digital Infrastructure: Local SEO & AI Search Visibility Research Archive

This repository contains the open datasets, deterministic verification scripts, figures, and technical appendices for original research published by **[580 Digital Infrastructure](https://580di.com)**, a Lawton-based marketing and web development agency serving Oklahoma businesses.

## Canonical Research Series (`580di.com/research`)

1. **[Report 001: Local AI Shortlist Report](https://580di.com/research/local-ai-shortlist-report)**
   * Explains how Google search results, Google Business Profile signals, reviews, and website pages shape local AI recommendations.
2. **[Report 002: Measuring AEO](https://580di.com/research/measuring-aeo)**
   * Defines practical measurement protocols for Answer Engine Optimization (AEO), separating single-prompt screenshot anecdotes from multi-prompt shortlist tracking and citation-share metrics.
3. **[Report 003: Beyond Citation Count (`/report-003`)](https://580di.com/research/beyond-citation-count)**
   * A 71-day empirical audit of 40,623 Microsoft Bing AI Performance page-citation records across 1,071 grounding queries. Demonstrates why raw page-citation totals overstate commercial visibility when non-commercial glossary pages absorb the majority of citations.
4. **[Report 004: The 2026 Oklahoma Local AI Shortlist Study (`/report-004`)](https://580di.com/research/oklahoma-local-ai-shortlist-study)**
   * An empirical study of 1,080 saved Gemini API responses with Google Search grounding across 15 Oklahoma cities, 12 local service categories, and 540 buyer-question pairs. Finds that the first business named changed in 78.0% of paired prompts and average shortlist overlap was 27.6%.

## Reproducing the Findings Offline

### Report 004 (`report-004/`)

Run the zero-network verification script to check SHA-256 file hashes and recompute all headline metrics directly from the saved CSV and JSON records:

```bash
cd report-004
python3 verify_reproducibility.py
```

### Report 003 (`report-003/`)

Run the analysis script to recompute all derived metrics from the exported Bing Webmaster Tools CSV tables:

```bash
cd report-003
python3 analyze.py
```

## Author & Organization

* **Author:** Jesse (Founder, 580 Digital Infrastructure)
* **Organization:** [580 Digital Infrastructure](https://580di.com) (Lawton, Oklahoma)
* **Research Hub:** [https://580di.com/research](https://580di.com/research)
* **AI Search & AEO Services:** [https://580di.com/services/ai-search-visibility](https://580di.com/services/ai-search-visibility)
