#!/usr/bin/env python3
"""
580 Digital Infrastructure - Report 004 Batch Study Runner
Collects new observations for the configured 15-city, 12-category study.
This optional live collector requires requests and a GEMINI_API_KEY environment variable.
Use study_analyzer.py to reproduce the archived results offline without credentials.

Also crawls and inspects the live websites of seed businesses and discovered local business domains.
Saves complete raw observations, CSV datasets, and summary statistics for Report 004.
"""

import concurrent.futures
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple
from urllib.parse import urlparse

import requests

# Import core inspector & environment from benchmarker.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from benchmarker import ENV, inspect_website, query_gemini_grounded

OUT_DIR = os.environ.get("REPORT004_OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "fresh-observations"))
CONFIG_PATH = os.environ.get("REPORT004_CONFIG", os.path.join(os.path.dirname(__file__), "study_config.json"))

DIRECTORY_DOMAINS = {
    "yelp.com", "bbb.org", "angi.com", "angieslist.com", "homeadvisor.com",
    "thumbtack.com", "nextdoor.com", "facebook.com", "instagram.com",
    "linkedin.com", "yellowpages.com", "mapquest.com", "birdeye.com",
    "chamberofcommerce.com", "expertise.com", "threebestrated.com",
    "buildzoom.com", "houzz.com", "porch.com", "networx.com", "manta.com",
    "google.com", "youtube.com", "reddit.com", "tiktok.com", "yahoo.com",
    "superpages.com", "cylex.us.com", "dnb.com", "buzzfile.com",
    "homestars.com", "trustpilot.com", "glassdoor.com", "indeed.com",
    "oklahoma.gov", "cib.ok.gov", "lawtonok.gov", "okc.gov", "yukonok.gov",
    "clutch.co", "upcity.com", "designrush.com", "semrush.com", "ahrefs.com",
    "goodfirms.co", "bark.com", "alignable.com"
}


def detect_platform(html_text: str, headers: Dict[str, str], robots_text: str) -> str:
    lower_html = html_text.lower()
    lower_robots = (robots_text or "").lower()
    if "townsquareinteractive.com" in lower_html or "tsi-disallow" in lower_robots or "/_dm/s/rt/" in lower_robots:
        return "Townsquare Interactive / Duda"
    if "hibu" in lower_html or "hibu" in lower_robots:
        return "Hibu / Duda"
    if "/_dm/s/rt/" in lower_html or "dmbody" in lower_html or "dudaone" in lower_html:
        return "Duda Website Builder"
    if "wix.com" in lower_html or "wixstatic.com" in lower_html:
        return "Wix"
    if "squarespace.com" in lower_html or "static1.squarespace.com" in lower_html:
        return "Squarespace"
    if "wp-content" in lower_html or "wp-includes" in lower_html:
        return "WordPress"
    if "webflow" in lower_html:
        return "Webflow"
    if "godaddy" in lower_html or "wsimg.com" in lower_html:
        return "GoDaddy Website Builder"
    if "/_next/static" in lower_html or "__next" in lower_html:
        return "Next.js / Custom"
    return "Custom / Other HTML"


def extract_clean_shortlist_from_text(text):
    from analysis_core import extract_candidates
    return extract_candidates(text)



def normalize_domain_from_title(title: str) -> str:
    """
    In Gemini Google Search groundingChunks, `web.title` is very often the bare domain
    (e.g. 'lawtonroofers.com', '580di.com', 'yelp.com').
    """
    t = (title or "").strip().lower()
    if re.match(r"^[a-z0-9.-]+\.[a-z]{2,10}$", t) and " " not in t:
        return t.replace("www.", "")
    return ""


def jaccard_similarity(list_a, list_b):
    from analysis_core import jaccard_similarity as overlap
    return overlap(list_a, list_b)



def run_single_query_task(task: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    prompt = task["prompt"]
    for attempt in range(3):
        res = query_gemini_grounded(prompt, api_key)
        if res.get("status") == "success" and res.get("text"):
            shortlist = extract_clean_shortlist_from_text(res["text"])
            chunk_domains = []
            directory_count = 0
            other_domain_count = 0
            for s in res.get("sources", []):
                dom = normalize_domain_from_title(s.get("title", ""))
                if dom:
                    chunk_domains.append(dom)
                    if any(dom == d or dom.endswith("." + d) for d in DIRECTORY_DOMAINS):
                        directory_count += 1
                    else:
                        other_domain_count += 1
            return {
                **task,
                "status": "success",
                "search_queries_run": res.get("search_queries_run", []),
                "search_query_count": len(res.get("search_queries_run", [])),
                "sources": res.get("sources", []),
                "source_count": len(res.get("sources", [])),
                "source_domains": list(dict.fromkeys(chunk_domains)),
                "directory_source_count": directory_count,
                "other_domain_source_count": other_domain_count,
                "shortlisted_entities": shortlist,
                "shortlist_count": len(shortlist),
                "first_listed_entity": shortlist[0] if shortlist else "",
                "response_text": res.get("text", ""),
                "observed_at_utc": datetime.utcnow().isoformat() + "Z",
                "generation_config_sent": res.get("generation_config_sent", {}),
                "raw_api_response": res.get("raw_api_response", {})
            }
        time.sleep(2 * (attempt + 1))
    return {
        **task,
        "status": "error",
        "error": res.get("error", "Unknown error"),
        "search_queries_run": [],
        "search_query_count": 0,
        "sources": [],
        "source_count": 0,
        "source_domains": [],
        "directory_source_count": 0,
        "other_domain_source_count": 0,
        "shortlisted_entities": [],
        "shortlist_count": 0,
        "first_listed_entity": "",
        "response_text": ""
    }


def inspect_site_enhanced(url: str, city: str) -> Dict[str, Any]:
    base = inspect_website(url)
    if not base.get("inspected") or "error" in base:
        base["platform"] = "Unreachable / Error"
        base["city_in_title_or_h1"] = False
        base["city_in_h2"] = False
        base["is_dead_or_parked"] = True
        return base

    # Check platform and city alignment
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    }
    raw_html = ""
    try:
        r = requests.get(base.get("final_url", url), headers=headers, timeout=12)
        raw_html = r.text
    except Exception:
        pass

    platform = detect_platform(raw_html, {}, base.get("robots_excerpt", ""))
    title_str = (base.get("title") or "").lower()
    h1_str = " ".join(base.get("h1s", [])).lower()
    h2_str = " ".join(base.get("h2s", [])).lower()
    city_lower = city.lower()

    city_in_title_or_h1 = (city_lower in title_str) or (city_lower in h1_str)
    if city_lower == "oklahoma city":
        city_in_title_or_h1 = city_in_title_or_h1 or ("okc" in title_str) or ("okc" in h1_str)

    city_in_h2 = (city_lower in h2_str) or (city_lower == "oklahoma city" and "okc" in h2_str)

    is_dead = (
        base.get("status_code", 200) >= 400
        or "no longer available" in raw_html.lower()
        or base.get("word_count_estimate", 0) < 40
    )

    base["platform"] = platform
    base["city_in_title_or_h1"] = city_in_title_or_h1
    base["city_in_h2"] = city_in_h2
    base["is_dead_or_parked"] = is_dead
    base["internal_page_count"] = len(base.get("internal_paths", []))
    base["has_schema"] = any(t != "Unparseable JSON-LD block" for t in base.get("schema_types", []))
    base["has_license_on_home"] = len(base.get("license_mentions_on_homepage", [])) > 0
    return base


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    api_key = ENV.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY missing")
        sys.exit(1)

    # Load any existing cached runs from raw_1080_runs.json, raw_480_runs.json, or raw_90_runs.json
    cached_by_key: Dict[Tuple[str, str, str, int], Dict[str, Any]] = {}
    for fname in ["raw_90_runs.json", "raw_480_runs.json", "raw_1080_runs.json"]:
        fpath = os.path.join(OUT_DIR, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    old_runs = json.load(f)
                for r in old_runs:
                    if r.get("status") == "success" and r.get("response_text"):
                        key = (r["city"], r["category_id"], r["intent_id"], int(r["paraphrase_index"]))
                        cached_by_key[key] = r
            except Exception as e:
                print(f"Warning reading {fpath}: {e}")

    tasks: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []
    run_id = 0
    for market in config["markets"]:
        city = market["city"]
        market_id = market["id"]
        for cat in config["categories"]:
            cat_id = cat["id"]
            cat_name = cat["name"]
            cib_reg = cat["cib_regulated"]
            for intent in cat["intents"]:
                intent_id = intent["intent_id"]
                intent_name = intent["intent_name"]
                for p_idx, prompt_tmpl in enumerate(intent["prompts"], 1):
                    run_id += 1
                    prompt = prompt_tmpl.replace("{city}", city)
                    key = (city, cat_id, intent_id, p_idx)
                    if key in cached_by_key:
                        cached_item = dict(cached_by_key[key])
                        cached_item["run_id"] = run_id
                        cached_item["market_id"] = market_id
                        cached_item["category_name"] = cat_name
                        cached_item["cib_regulated"] = cib_reg
                        cached_item["intent_name"] = intent_name
                        results.append(cached_item)
                    else:
                        tasks.append({
                            "run_id": run_id,
                            "market_id": market_id,
                            "city": city,
                            "category_id": cat_id,
                            "category_name": cat_name,
                            "cib_regulated": cib_reg,
                            "intent_id": intent_id,
                            "intent_name": intent_name,
                            "paraphrase_index": p_idx,
                            "prompt": prompt
                        })

    total_expected = len(results) + len(tasks)
    print(f"=== Starting 580DI Report 004 Batch Study: {total_expected} Total Queries ({len(results)} cached, {len(tasks)} to run) ===")
    t_start = time.time()

    def save_checkpoint(current_results: List[Dict[str, Any]]):
        sorted_res = sorted(current_results, key=lambda x: x["run_id"])
        for out_name in ["raw_1080_runs.json"]:
            out_path = os.path.join(OUT_DIR, out_name)
            with open(out_path, "w", encoding="utf-8") as out_f:
                json.dump(sorted_res, out_f, indent=2)

    if tasks:
        completed_new = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            future_to_task = {executor.submit(run_single_query_task, t, api_key): t for t in tasks}
            for future in concurrent.futures.as_completed(future_to_task):
                res = future.result()
                results.append(res)
                completed_new += 1
                print(f"[{len(results):04d}/{total_expected}] Run #{res['run_id']:04d} ({res['city']} - {res['category_id']}): "
                      f"queries={res['search_query_count']}, sources={res['source_count']}, "
                      f"shortlisted={res['shortlist_count']} -> {res['shortlisted_entities'][:3]}", flush=True)
                if completed_new % 30 == 0:
                    save_checkpoint(results)

    save_checkpoint(results)
    print(f"\nSaved {len(results)} total raw runs to {OUT_DIR}/raw_1080_runs.json in {int(time.time() - t_start)}s.", flush=True)


if __name__ == "__main__":
    main()

