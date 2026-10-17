"""Deterministic, offline extraction rules for Report 004.

Outputs are name candidates, not verified businesses or endorsements. No fuzzy
token matching, random set traversal, or arbitrary shortlist-length cutoff.
"""
import re
import unicodedata

GENERIC_LABELS = {
    'note', 'key', 'important', 'summary', 'services', 'why', 'pros', 'cons',
    'location', 'phone', 'address', 'website', 'specialties', 'overview',
    'what to look for', 'questions to ask', 'licensing', 'insurance',
    'oklahoma cib license', 'cib license', 'reviews', 'reputation',
    'free estimates', 'warranty', 'experience', 'local presence',
    'key services', 'why they stand out', 'what they do', 'highlights',
    'things to consider', 'next steps', 'tip', 'tips', 'recommendation',
    'recommendations', 'top picks', 'notable mentions', 'other options',
    'reviews and reputation', 'licensing and insurance', 'customer service',
    'service area', 'services offered', 'customer reviews', 'years in business',
    'affordable and flexible pricing', 'affordable auto insurance',
    'affordable care act (aca) plans', 'national providers', 'home protection',
    'warranty and materials', 'services relevant to small businesses',
    'lawn care companies', 'landscaping companies', 'family health insurance',
    'bathroom remodeling & walk-in shower specialists', 'bundling for savings',
    'focus on google business profile optimization', 'strategies for affordability',
    'agencies highly rated by expertise.com', 'individual agents with specific mentions of roof coverage',
    'local marketing companies & their specializations',
    'general electrician services (including upgrades and repairs)', 'tile specific specialists',
    'services with strong customer satisfaction for reliability',
    'lawn care & landscaping companies in midwest city, ok',
    'dedicated bathroom remodelers & tile specialists',
    'general remodeling contractors with bathroom expertise', 'digital and specialized services',
    'specialized drainage solution providers (may serve enid)',
    'individual cleaners mentioned in community discussions',
    'local agencies and experts serving owasso, ok',
    'independent insurance agencies for comprehensive comparisons',
    'bundling for family insurance savings (auto and home/renters)',
    'family health insurance in owasso, ok',
    'broader marketing agencies (also serving small businesses)',
    'shawnee, ok focused seo companies', 'specialized cleaning companies',
    'companies emphasizing trust and positive feedback',
    'independent insurance agencies (to compare multiple quotes)',
    'local agents for specific companies',
    'companies noted for potentially lower rates in shawnee',
    'tile and flooring specialists with shower expertise',
    'lawn care & landscaping companies in ardmore, ok',
    'agencies and agents mentioned as top-rated or notable',
    'broader oklahoma and national providers with relevant services',
    'finding freelancers and agencies',
    'major insurance providers with local agents',
    'approach', 'contact', 'warranties', 'inspections', 'guarantees',
    'communication', 'budget', 'deductibles', 'comprehensive services',
    'comprehensive gbp optimization', "understanding of google's policies",
    'clear strategy and transparency', 'understanding of the industry',
    'transparent communication and support', 'specialized health insurance agencies',
    'understanding of the ardmore market', 'pricing', 'cost', 'service offerings',
}

# Explicit brand aliases; service words and geographic qualifiers are retained.
ALIASES = {
    '580 digital': '580 digital infrastructure',
    'webb branding': 'webb branding',
    'rsi roofing services': 'rsi roofing services',
}

def normalize_name(name):
    name = unicodedata.normalize('NFKC', name).lower().replace('’', "'")
    name = name.replace('&', ' and ').replace("'", '')
    name = re.sub(r'[^a-z0-9]+', ' ', name).strip()
    # Remove terminal legal suffixes only, never substrings such as "co" in a brand.
    name = re.sub(r'(?:\s+(?:llc|incorporated|inc|ltd|corp|corporation))+$', '', name)
    return ALIASES.get(name, name)

def rejection_reason(name):
    n = name.lower().strip(' :.')
    if len(n) < 2 or len(n) > 140:
        return 'length'
    if n in GENERIC_LABELS:
        return 'generic label'
    if re.match(r'^(?:top (?:marketing|lawn|landscaping|house|concrete|foundation|web)\b|platforms (?:for|to)\b|tips for\b|nationally recognized providers\b|established cleaning companies\b|affordable auto insurance providers\b|get (?:quotes|multiple|detailed|a quote)\b|confirm services\b|investigate\b|understand the\b|ask (?:for|about)\b|look for agents\b|compare quotes\b|work with independent agents\b|companies offering\b|circuit breaker repair in\b|electrician in\b)', n):
        return 'category heading or advice'
    if re.match(r'^(?:top[- ]rated\b|top recommendations\b|top recommended\b|top local\b|top contenders\b|key\s|other\s|recommended\s|recommendations\s|highly[- ]|for\s|additional\s|here are\s|companies (?:mentioned|known)|agencies (?:representing|offering)|agents (?:with|affiliated)|independent (?:agencies|insurance agencies are)|direct carriers\s|affordable family\s|general contractors\s|tile contractors with\s|broader seo agencies\s|specializing in\s|potential local\s|local and\s|local reputation\s|local experience\b|national providers\s|oklahoma-based seo companies\s)', n):
        return 'section heading'
    if re.match(r'^(?:read\s|review customer\s|inquire\s|understand their\s|consider (?!it fixed\b)|discuss their\s|finding affordable\s|hiring considerations\b|customer reviews\b|reputation (?:and|management)\b|reviews and\b|experience (?:and|with|in)\b|relevant experience\b|free estimates\b|important steps\b|yukon-specific and nearby options\b)', n):
        return 'advice or attribute heading'
    if n.endswith('?') or re.match(r'^(?:verify|check|always|make sure|how to|what to|when to|why you|questions to|important considerations)\b', n):
        return 'instruction or question'
    if re.match(r'^(?:electricians|contractors|companies|agencies|plumbers|roofers|mechanics|cleaners|landscapers)\s+(?:in|specializing|installing|offering|with|for)\b', n):
        return 'category heading'
    return ''

def extract_candidates(text):
    result, seen = [], set()
    for match in re.finditer(r'\*\*([^*\n]+)\*\*', text):
        name = re.sub(r'^(?:\d+[.)]\s*|#\d+\s*[-:]?\s*)', '', match.group(1)).strip().rstrip(':.').strip()
        reason = rejection_reason(name)
        key = normalize_name(name)
        if reason or not key or key in seen:
            continue
        split_names = {
            'USAA, Progressive, and Mercury': ['USAA', 'Progressive', 'Mercury'],
            'CommunityCare and Oscar': ['CommunityCare', 'Oscar'],
        }.get(name, [name])
        for part in split_names:
            part_key = normalize_name(part)
            if part_key not in seen:
                seen.add(part_key)
                result.append(part)
    return result

def jaccard_similarity(a, b):
    left, right = {normalize_name(n) for n in a}, {normalize_name(n) for n in b}
    union = left | right
    return len(left & right) / len(union) if union else None

def domain_match_reason(domain, title, name, seed_name=''):
    n = normalize_name(name)
    if seed_name and n == normalize_name(seed_name):
        return 'exact seed name'
    stem = domain.lower().removeprefix('www.').split('.')[0]
    compact = n.replace(' ', '')
    # Full normalized brand/domain-stem containment, not one shared token.
    if min(len(stem), len(compact)) >= 6 and (stem in compact or compact in stem) and min(len(stem), len(compact))/max(len(stem), len(compact)) >= .6:
        return 'full brand/domain stem'
    normalized_title = normalize_name(title)
    if len(compact) >= 8 and re.search(r'(?<!\w)' + re.escape(n) + r'(?!\w)', normalized_title):
        return 'full name phrase in title'
    if domain == '580di.com' and n == '580 digital infrastructure':
        return 'explicit published alias'
    if domain == 'okcbath.com' and n in {'parsons stone and tile', 'parsons stone tile'}:
        return 'explicit published alias'
    return ''
