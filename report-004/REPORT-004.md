# The 2026 Oklahoma Local AI Shortlist Study

**What 1,080 buyer questions show about local business visibility in AI search**

By Jesse Killian, 580 Digital Infrastructure LLC, Lawton, Oklahoma  
Research Report 004 · October 2026  
Exploratory observational study. Not peer reviewed.

---

## Abstract

Across **540 pairs of buyer questions** covering **15 Oklahoma cities and 12 service categories**, the first business name listed differed in **78.0%** of paired answers. Average overlap between the two sets of names was **27.6%**. Most names appeared in only one of the six questions asked within their city and service category.

This study examines **1,080 saved responses** from the Gemini API using Google Search grounding. Every prompt was written as an ordinary buyer question without naming any company. The results show wide variation from one answer to the next, and they show why a single screenshot is weak proof of local AI visibility.

These findings describe one AI setup and the questions we tested. They measure which names appeared in the answers, not customer preference, verified endorsements, phone calls, or sales.

## 1. The first name listed changed in 78% of paired answers

A business owner might ask an AI assistant who to hire, see a competitor listed first, and assume that competitor owns the market. The next customer can ask for the same service in slightly different words and see a different company at the top of the list.

In this study, we wrote two everyday phrasings for each buyer need. Across all **540 pairs**, the first provider name extracted from the answer:

- **Agreed in 119 pairs (22.0%).**
- **Differed in 421 pairs (78.0%).**

We track the first name in the list because that is the first business a reader sees. Being listed first does not mean the assistant ranked that company as the best option. Many responses offered a short list of local providers without claiming a formal number one ranking.

Comparing two phrasings also captures ordinary model and search retrieval variation alongside the wording change itself. The study does not separate how much of the difference came from the phrasing alone versus normal run to run variation. What it does show is simple: two natural ways of asking for the same local service usually produced a different opening name.

For a business owner, one answer is a very small sample. It takes a broader set of customer questions to know whether a single appearance or absence reflects a real pattern.

## 2. The names in paired answers overlapped by 27.6% on average

The variation went well beyond the first name on the page. For each pair of questions, we compared the full set of extracted business names using Jaccard overlap, which divides the number of shared names by the total distinct names across both answers.

Across the 540 pairs:

- **Mean overlap: 27.6%.**
- **Median overlap: 25.0%.**

For example, if one answer names companies A, B, and C, and the paired answer names B, C, and D, two names are shared out of four total names across the pair, which equals 50% overlap.

An average overlap of 27.6% shows low agreement between paired answers. Because Jaccard overlap uses the combined set of names from both answers as its denominator, a 27.6% score should not be read as saying that 72.4% of a single list was replaced.

Before comparing lists, we normalized business names for case, punctuation, ampersands, apostrophes, and legal endings such as LLC or Inc. We kept service words and city names intact so distinct local businesses would not be merged by mistake. As a result, spelling variations or branch names can still count as separate entries. The full name lists and matching rules are included in the data package.

## 3. Most names appeared in only one of six questions

Within each city and service category, we asked **six questions covering three common buyer needs, each phrased two ways**. A roofing contractor might be named for a hail claim question, for instance, without being named for a leak repair question.

Across the 180 city and category cells, the responses produced **4,804 distinct city, category, and name combinations**. If the same company was named in two different cities, it was counted once in each city cell, so 4,804 is the number of cell appearances rather than 4,804 separate companies statewide.

| Questions where a name appeared | City, category, and name combinations | Share |
| --- | ---: | ---: |
| 1 of 6 prompts | 2,906 | 60.5% |
| 2 of 6 prompts | 945 | 19.7% |
| 3 of 6 prompts | 463 | 9.6% |
| 4 of 6 prompts | 249 | 5.2% |
| 5 of 6 prompts | 156 | 3.2% |
| 6 of 6 prompts | 85 | 1.8% |

**80.2% appeared in only one or two questions. Only 5.0% appeared in five or six.**

This table measures how broadly a name showed up across the six questions in its category, not whether repeating the exact same prompt six times gives the same output. A business can appear in only one or two prompts simply because it specializes in one kind of work.

For an owner, that distinction matters. The goal is not just whether an AI tool has heard of the business, but whether the business shows up when customers ask about the specific jobs it wants to book.

## 4. Agreement stayed low across all twelve service categories

Every service category included 90 responses and 45 paired comparisons across the state. Average overlap between paired answers ranged from **14.5% in insurance** to **35.1% in house cleaning**. Not a single category averaged 50% overlap under our comparison rules.

| Service category | Mean name overlap | First name agreed |
| --- | ---: | ---: |
| House cleaning | 35.1% | 14 of 45 (31.1%) |
| Electrical | 33.9% | 12 of 45 (26.7%) |
| Foundation / concrete | 33.1% | 8 of 45 (17.8%) |
| Pest control | 32.1% | 12 of 45 (26.7%) |
| HVAC | 28.9% | 7 of 45 (15.6%) |
| Local marketing / SEO / web | 28.7% | 15 of 45 (33.3%) |
| Roofing | 28.5% | 6 of 45 (13.3%) |
| Plumbing | 27.5% | 11 of 45 (24.4%) |
| Auto repair | 26.0% | 13 of 45 (28.9%) |
| Showers / remodeling | 23.2% | 9 of 45 (20.0%) |
| Lawn / landscaping | 19.6% | 8 of 45 (17.8%) |
| Insurance | 14.5% | 4 of 45 (8.9%) |

These category numbers do not rank which trades are harder or easier to market. In insurance, for example, one answer might name an individual local agent while the paired answer names the agency or the national carrier, which lowers exact name agreement. Other categories have their own naming quirks and service overlaps.

The 15 cities tested were Oklahoma City, Tulsa, Norman, Broken Arrow, Edmond, Lawton, Moore, Midwest City, Enid, Stillwater, Owasso, Shawnee, Ardmore, Duncan, and Yukon. Each city had 72 responses and 36 paired comparisons. All city and category tables are included in the download package.

## 5. What the grounding source records show

Across the 1,080 responses, the API recorded **2,962 search query strings** and **8,370 grounding source entries**, an average of **2.74 searches** and **7.75 source entries per response**.

Those records make it possible to inspect what the system searched for and which web pages were attached to the response alongside the companies named in the answer. Being listed as a source in the metadata and being recommended by name in the visible answer are two separate things, and one does not guarantee the other.

The grounding records include local business domains, directories, marketplaces, social pages, news sites, and other web pages. Because we did not manually verify legal ownership for every domain in the 8,370 source entries, this study does not claim an exact percentage of websites owned by the businesses themselves. Grounding source entries also count every appearance across responses rather than unique websites or visible links in the text.

We also saved website inspection records for **1,667 candidate domains** surfaced during the study. Exploratory comparisons of those websites are covered in the technical appendix. They describe patterns in the sample, not a guaranteed formula for getting recommended.

## 6. What this means for an Oklahoma business

The practical takeaway is that showing up once in an AI chat window is very different from showing up consistently across the questions real customers ask.

Anyone evaluating local AI visibility should look at the exact questions asked, when they were run, the full text of the answers, the businesses named, and the sources attached. One cherry picked screenshot proves very little. And if someone claims a website change improved AI visibility, that claim needs to be tested across a fixed set of buyer questions before and after the work.

Accuracy matters just as much as frequency. In our dataset, answers sometimes drifted into neighboring trades, mixed national brands with local shops, or listed individual agents next to company names. Being mentioned only helps when the assistant describes the right service in the right town for the right kind of customer.

This study does not prove that adding schema markup, writing longer pages, or putting a city name into a heading forces an AI assistant to recommend a business. Nor does it prove that an AI mention turns into a phone call or a signed job. Those questions require controlled testing and real lead tracking.

## 7. Scope and access to the evidence

This report captures a point in time for **one specific setup: `gemini-2.5-flash` called through the Gemini API with Google Search grounding**. It does not measure ChatGPT, Perplexity, Microsoft Copilot, the consumer Gemini web app, or Google AI Overviews.

Because each pair tested two wordings without repeating identical prompts side by side, the results measure total observed variation between paired answers rather than isolating phrasing as a single cause. Automated name extraction and conservative matching also have edge cases, and we did not manually verify every business named across all 15 cities.

The [technical appendix](/research/report-004/TECHNICAL-APPENDIX.md) walks through the exact methods, website comparisons, statistical tests, and limitations. The open research package includes all 1,080 saved answers and source lists, the exact prompts, extracted name tables, paired comparisons, website inspection records, and offline Python scripts so anyone can check the numbers without giving an email address.

[Download the research package files](#data-downloads).
