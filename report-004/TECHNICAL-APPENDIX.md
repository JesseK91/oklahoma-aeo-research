# Report 004: Technical Appendix

Methods, statistical details, and limits for the 2026 Oklahoma Local AI Shortlist Study.

## Study design

The fifteen markets are Oklahoma City, Tulsa, Norman, Broken Arrow, Edmond, Lawton, Moore, Midwest City, Enid, Stillwater, Owasso, Shawnee, Ardmore, Duncan, and Yukon. Each city has 72 prompts. The twelve service categories are roofing; HVAC; plumbing; electrical; showers and bathroom remodeling; pest control; auto repair; local marketing, SEO, and web design; house cleaning; lawn care and landscaping; foundation and concrete work; and insurance. Each category has 90 prompts.

Every category contains three distinct buyer intents, and each intent is written in two natural wordings. The exact prompts and configured seed sites are available in [study_config.json](/research/report-004/study_config.json). Company names were never inserted into the buyer prompts. Having the configuration file in the archive documents the design we ran, though it does not constitute an independently timestamped preregistration.

The collection script queried `gemini-2.5-flash` through the Gemini API with Google Search grounding enabled. **Temperature was not explicitly set in the collection script.** Our study notes record the collection run on October 16 and 17, 2026, though individual execution timestamps, complete raw API envelopes, and an immutable returned model version string were not saved. All calculations in this report run offline against those saved observations rather than issuing new API requests or crawling live websites again.

### Name extraction and identity rules

The parser extracts bolded name candidates from each answer, filters out generic section headings and conversational advice, keeps provider names that contain category words, and applies no ten name cap. All ten responses that returned without bold markup were manually transcribed in the order the names appeared. Run 1008 also uses a manual transcription because its opening insurance agents appeared in plain text and its closing bold sentence combined two people. Every manual transcription is published in [manual_name_overrides.json](/research/report-004/manual_name_overrides.json).

Extracted names are normalized for letter case, punctuation, ampersands, apostrophes, and common legal suffixes such as LLC or Inc. Geographic qualifiers and service words are kept intact, and the explicit alias map is small. **We do not use fuzzy token matching.** Because of that, spelling variations or branch labels can remain separate entries, which can lower measured overlap and raise the total count of distinct names. Extracting names from bold formatting can also miss an unbolded business mention inside an otherwise formatted answer, or retain a descriptive phrase alongside a name. We publish the full [extracted name ledger](/research/report-004/extracted_names.csv) so anyone can inspect these choices row by row.

When we refer to the first name listed, we mean the first extracted name in the response text. The prompt did not require the model to rank companies from best to worst, and the first name in an answer can be a national brand, an individual insurance agent, or an adjacent service provider. We do not treat first position as a definitive endorsement. Some responses also drifted into adjacent categories, and we kept those responses in the dataset as part of the observed behavior.

### Metrics and denominators

**Prompt coverage** counts how many of the six prompts in a given city and category cell include a normalized business name. A business that appears in only one of the six prompts is not necessarily suffering from random instability; it may simply fit only one of the three specific jobs asked about in that category. Because this dataset does not repeat the exact same prompt multiple times, it cannot separate wording sensitivity from repeated prompt reliability.

**Jaccard overlap** divides the number of shared normalized names in a pair of answers by the combined set of distinct names across both answers. If both answers in a pair had returned zero names, the pair would be undefined and excluded rather than counted as a match. In our dataset, all 540 pairs contained extracted names on both sides, giving 540 comparable pairs for both Jaccard overlap and first name agreement. A mean Jaccard score of 27.6% does not mean that 72.4% of a single list changed, because the denominator is the combined union of both lists.

**Grounding source entries** are the records saved from `groundingChunks` on each response. The same website domain can appear across many responses or appear multiple times within a single response. These counts measure saved source records, not unique websites, unique businesses, or visible inline links. In Google's API documentation, `groundingSupports` maps specific answer passages to specific source chunks; that passage mapping was not saved in our archive. See [Google's grounding documentation](https://ai.google.dev/gemini-api/docs/google-search/).

## Website signal analysis

The frozen website inspection table contains **1,667 candidate domains** gathered from the grounding source records and the configured seed list. It is not a random sample of Oklahoma businesses, and we did not independently verify local ownership or physical storefront status for every domain. The table includes national brands, out of state companies, and directory or editorial sites. During inspection, **1,429 domains returned HTTP 200**. The original crawler also filtered out pages flagged as unavailable or containing fewer than 40 extracted words, leaving **1,365 eligible candidate sites** for the signal comparisons. Returning HTTP 200 with 40 words of text does not by itself prove that a site is an active local business.

To stay consistent with the frozen city text flags, each domain keeps its original primary city and category assignment, which was typically the first cell where the crawler encountered it. A domain that appeared in several Oklahoma cities is counted once in this site table, and its matched prompt count reflects only the six prompts in that primary cell.

We link a candidate domain to an extracted business name only when a configured seed name matches, an explicit alias applies, a sufficiently long brand and domain stem matches, or the full normalized business name appears in the saved homepage title. Ambiguous cases are left unlinked. This conservative automated rule avoids false merges, but it is not a complete verified business registry. **Having no matched name in our table does not prove that the business behind that website was absent from the AI answers.** Missing aliases, unbolded mentions, and truncated homepage titles can all leave a mentioned business unlinked. In addition, because homepage titles are one of the inputs used to link domains to extracted names, associations involving title text can be upward biased.

Under these linking rules, the 1,365 eligible sites fall into three groups: **311 sites matched to names in 3 to 6 prompts**, **685 sites matched in 1 to 2 prompts**, and **369 sites with no conservative name match**. Every linking decision, including ambiguous and unmatched rows, is published in [domain_name_matches.csv](/research/report-004/domain_name_matches.csv).

The geographic text flags record whether the target city name (including common abbreviations such as OKC for Oklahoma City) appeared in the homepage title or H1, or in an H2 heading. They do not verify whether the heading grammatically connects the company name, service, and city. The schema flag records whether the HTML parser found at least one parseable JSON-LD `@type` value, ignoring unparseable script blocks. It does not verify Schema.org vocabulary compliance, required fields, factual accuracy, or Google rich result eligibility.

| Website signal | Matched in 3 to 6 prompts | No matched name | Unadjusted odds ratio (95% CI) | Raw p | Holm adjusted p | Cell bootstrap difference 95% CI (percentage points) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Target city in title or H1 | 216/311 (69.5%) | 124/369 (33.6%) | 4.49 (3.25 to 6.21) | 1.23e-20 | 6.14e-20 | 27.26 to 43.94 |
| Target city in H2 | 110/311 (35.4%) | 57/369 (15.4%) | 3.00 (2.08 to 4.32) | 1.82e-09 | 7.29e-09 | 13.28 to 26.97 |
| At least one parseable JSON-LD @type | 267/311 (85.9%) | 296/369 (80.2%) | 1.50 (0.99 to 2.25) | 0.0524 | 0.105 | 0.03 to 11.71 |

Raw p-values come from two-sided two-proportion Z-tests. Odds ratio confidence intervals use standard unadjusted log-Wald intervals, adding a 0.5 continuity correction only when a cell count is zero. Holm adjustment is applied across the five exploratory homepage checks: the three binary proportions in the table above, homepage word count, and capped internal link count. Because sites within the same city and category share prompts, we also resampled the primary city and category cells 2,000 times with a fixed random seed and report the 95% percentile intervals for the percentage point differences. Those cluster bootstrap intervals account for shared cell grouping, though they do not adjust for confounding variables.

Median homepage word counts were **882** in the 3 to 6 prompt group versus **970** in the unmatched group, with a Mann-Whitney **p = 0.114**. Failing to find a statistically significant difference does not prove that the two groups have identical copy length or establish a minimum word count threshold. Median recorded internal link counts were **22** versus **26** (**p = 0.00601**), where the inspection script capped its saved link list at 30 per page. That capped count reflects homepage link density up to 30 links rather than total site size, and it is not evidence that adding internal links hurts visibility.

For the parseable JSON-LD `@type` check, the raw comparison gave **p = 0.0524** and the Holm adjusted test gave **p = 0.105**. The standard odds ratio confidence interval crosses 1.0, while the cluster bootstrap interval sits just above zero, showing how sensitive a borderline difference is to the choice of interval estimator. Taken together, the data do not show a clear difference in basic JSON-LD presence after multiple testing adjustment.

The city text differences in titles, H1s, and H2s are large in this sample, but they remain observational associations. They do not prove that adding a city name to a heading causes an AI model to recommend a business, nor do they show that headings matter more than underlying search rankings, brand reputation, review volume, or domain authority. City size, service category, organic search rank, and our title-assisted name linking rule can all contribute to the observed gap.

## Limitations

This study examines one model and search grounding configuration (`gemini-2.5-flash` via the Gemini API) over a single collection window. It does not include repeated identical prompts, randomized prompt order, an independently timestamped preregistration, full raw API response envelopes, verified business ownership across all 8,370 source entries, or downstream customer conversion data. Checksums and p-values verify the math on our saved files, but they do not remove those boundaries.

Any automated name matching rule faces a tradeoff: strict normalization can split two variations of the same local business, while loose matching can merge unrelated companies that share common trade words. Future releases can build on this baseline by testing multiple AI engines, running repeated identical prompts across several dates, and auditing a fixed panel of verified Oklahoma businesses over time.

For an Oklahoma business owner, the practical takeaway is straightforward. Instead of relying on a single test prompt, check a realistic set of six to ten customer questions across the services you actually sell, see which websites the answer engine cites when it builds the list, and make sure your own pages state clearly what you do and which Oklahoma towns you serve.
