#!/usr/bin/env python3
"""Render the four Report 004 SVG figures from study_summary.json only."""
import argparse, html, json
from pathlib import Path
PAPER='#f3ead8';SURFACE='#fff9ed';INK='#11100e';MUTED='#655d51';ORANGE='#f05a24'
def esc(s):return html.escape(str(s))
def text(x,y,s,size=18,color=INK,weight=400):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{esc(s)}</text>'
def svg(title,description,parts):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 1200 620" role="img" aria-labelledby="title desc"><title id="title">{esc(title)}</title><desc id="desc">{esc(description)}</desc><rect width="1200" height="620" fill="{PAPER}"/><g font-family="Arial, sans-serif">'+''.join(parts)+'</g></svg>\n'
def header(number,title,subtitle):return [text(60,45,f'REPORT 004 / FIGURE {number}',15,ORANGE,700),text(60,96,title,32,INK,700),text(60,133,subtitle,17,MUTED)]
def bar(x,y,width,color=INK,height=26):return f'<rect x="{x}" y="{y}" width="{max(0,width):.2f}" height="{height}" fill="{color}"/>'
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parent);ap.add_argument('--output-dir',type=Path)
    a=ap.parse_args();s=json.loads((a.data_dir/'study_summary.json').read_text());out=a.output_dir or a.data_dir/'figures';out.mkdir(parents=True,exist_ok=True)
    d=s['prompt_coverage_distribution'];N=s['total_unique_cell_business_appearances'];parts=header(1,'How widely did names appear across six different prompts?',f'{N:,} distinct city, category, and name combinations across three buyer intents.')
    for i in range(1,7):
        v=d[str(i)];y=177+(i-1)*59;parts += [text(60,y+24,f'{i} of 6 prompts',19),bar(260,y,v['pct']*9,ORANGE if i>=3 else INK,32),text(290+v['pct']*9,y+24,f"{v['count']:,} ({v['pct']:.1f}%)",18)]
    parts += [text(60,582,'Prompt coverage measures presence across six questions in a cell, not repeated runs of one identical prompt.',17,MUTED)]
    files={'shortlist-repeatability-distribution.svg':svg('Name coverage across six buyer prompts','Counts of extracted names appearing in one through six prompts within a city and category.',parts)}
    changed=s['first_name_comparable_pairs']-s['first_name_matches']
    change_pct=100-s['first_name_agreement_comparable_pct']
    parts=header(2,'The first name listed changed in most paired answers',f"{s['paraphrase_pairs_tested']:,} pairs of buyer questions expressing the same service need.")
    parts += [text(70,245,f"{change_pct:.1f}%",76,ORANGE,700),text(70,295,'First name listed differed',27,INK,700),text(70,335,f"{changed} of {s['first_name_comparable_pairs']} paired answers",22,MUTED),text(70,380,f"Same first name: {s['first_name_matches']} pairs",20,MUTED)]
    parts += [text(665,245,f"{s['mean_paraphrase_jaccard_overlap_pct']:.1f}%",76,ORANGE,700),text(665,295,'Mean name overlap',27,INK,700),text(665,335,'Jaccard: shared names / combined set',20,MUTED),text(665,380,f"Median: {s['median_paraphrase_jaccard_overlap_pct']:.1f}%",20,MUTED)]
    parts += [text(60,540,'Names are compared under the published normalization rules; spelling variants can remain separate.',17,MUTED),text(60,578,'Paired differences reflect both prompt wording and ordinary model and search retrieval variation.',17,MUTED)]
    files['paraphrase-overlap-and-sources.svg']=svg('First name differences and name overlap in paired answers','The first extracted name differed in most paired answers; Jaccard overlap across the full name lists is also shown.',parts)
    a1=s['tier_3_6_leaders_stats'];b1=s['tier_0_unmatched_stats'];parts=header(3,'Homepage signals across matched name groups',f"3 to 6 matched prompts: n={a1['count']}; no matched name: n={b1['count']}. Name linking is conservative.")
    for i,(field,label) in enumerate([('city_in_title_or_h1','Target city in title or H1'),('city_in_h2','Target city in H2'),('has_parseable_schema_type','At least one parseable JSON-LD @type')]):
        y=189+i*112;v=a1['pct_'+field];w=b1['pct_'+field];parts += [text(60,y,label,20,INK,700),bar(500,y-19,v*5.4,ORANGE),text(520+v*5.4,y+1,f'{v:.1f}%',17),bar(500,y+17,w*5.4,INK),text(520+w*5.4,y+37,f'{w:.1f}%',17)]
    parts += [text(60,546,'Orange: matched in 3 to 6 prompts. Black: no conservative match in the primary cell.',17,MUTED),text(60,578,'Observational homepage comparisons; does not establish a causal effect or full schema validity.',17,MUTED)]
    files['website-signals-by-shortlist-tier.svg']=svg('Homepage signals by matched name group','Target city text and parseable JSON-LD type rates across comparison groups.',parts)
    labels={'auto_repair':'Auto repair','electrical':'Electrical','foundation_concrete':'Foundation / concrete','house_cleaning':'House cleaning','hvac':'HVAC','insurance':'Insurance','lawn_landscaping':'Lawn / landscaping','local_marketing':'Local marketing','pest_control':'Pest control','plumbing':'Plumbing','roofing':'Roofing','shower_remodeling':'Showers / remodeling'}
    parts=header(4,'Name agreement across all twelve service categories','Orange: mean Jaccard overlap. Black: same first name listed. 45 paired comparisons per category.')
    for i,row in enumerate(s['category_breakdown']):
        y=164+i*33;v=row['mean_jaccard_overlap_pct'];w=row['first_name_agreement_pct'];parts += [text(60,y+14,labels[row['category']],17),bar(310,y,v*10,ORANGE,10),bar(310,y+13,w*10,INK,10),text(920,y+16,f'{v:.1f}% / {w:.1f}%',16)]
    parts += [text(60,598,'Observed in one Gemini API configuration; other AI tools and live web indices can differ.',16,MUTED)]
    files['category-shortlist-stability.svg']=svg('Paired name agreement by service category','Mean Jaccard overlap and first name agreement across twelve local service categories.',parts)
    for name,content in files.items():(out/name).write_text(content)
    print(f'Generated {len(files)} figures from {a.data_dir / "study_summary.json"}')
if __name__=='__main__':main()
