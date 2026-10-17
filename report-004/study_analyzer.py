#!/usr/bin/env python3
"""Report 004 offline analysis. Standard library only; no credentials or network.
Run: python3 study_analyzer.py --input-dir . --output-dir derived
"""
import argparse, csv, hashlib, json, math, random, re, statistics
from collections import Counter, defaultdict
from pathlib import Path
from analysis_core import extract_candidates, normalize_name, jaccard_similarity, domain_match_reason

DIRECTORIES = set('yelp.com bbb.org angi.com angieslist.com homeadvisor.com thumbtack.com nextdoor.com facebook.com instagram.com linkedin.com yellowpages.com mapquest.com birdeye.com chamberofcommerce.com expertise.com threebestrated.com buildzoom.com houzz.com porch.com networx.com manta.com google.com youtube.com reddit.com tiktok.com yahoo.com superpages.com cylex.us.com dnb.com buzzfile.com homestars.com trustpilot.com glassdoor.com indeed.com clutch.co upcity.com designrush.com goodfirms.co bark.com alignable.com care.com homeaglow.com lawtonfortsillchamber.com normanchamber.com duncanchamber.com'.split())
REFERENCE = set('semrush.com ahrefs.com einnews.com valuenews.com pr.com wikipedia.org forbes.com usnews.com bobvila.com thisoldhouse.com nerdwallet.com bankrate.com consumerreports.org kswo.com kfor.com koco.com news9.com oklahoman.com tulsaworld.com'.split())

def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def source_domain(s):
    d=s.get('title','').strip().lower().removeprefix('www.')
    return d if re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,24}',d) else ''

def source_class(d):
    if not d:return 'unresolved'
    if d.endswith(('.gov','.edu','.mil')) or d.endswith('.ok.gov'):return 'government_or_education'
    if any(d==x or d.endswith('.'+x) for x in sorted(DIRECTORIES)):return 'listed_directory_social_or_marketplace'
    if any(d==x or d.endswith('.'+x) for x in sorted(REFERENCE)):return 'listed_publisher_or_reference'
    return 'other_domain_ownership_unverified'

def pct(n,d):return round(100*n/d,1) if d else None

def proportion(a,n,c,m):
    if not n or not m:return {'p_value':None,'odds_ratio':None}
    b,d=n-a,m-c
    aa,bb,cc,dd=tuple(v+.5 for v in (a,b,c,d)) if 0 in (a,b,c,d) else (a,b,c,d)
    odds=aa*dd/(bb*cc);sl=math.sqrt(sum(1/v for v in (aa,bb,cc,dd)));pool=(a+c)/(n+m)
    se=math.sqrt(pool*(1-pool)*(1/n+1/m));z=(a/n-c/m)/se if se else 0
    return {'success_leaders':a,'n_leaders':n,'success_unmatched':c,'n_unmatched':m,'odds_ratio':round(odds,3),
            'odds_ratio_95ci':[round(math.exp(math.log(odds)-1.96*sl),3),round(math.exp(math.log(odds)+1.96*sl),3)],
            'difference_percentage_points':round(100*(a/n-c/m),3),'z':round(z,3),'p_value':math.erfc(abs(z)/math.sqrt(2)),
            'interpretation':'exploratory unadjusted association; identity and independence assumptions apply'}

def mann_whitney(x,y):
    n,m=len(x),len(y);ordered=sorted([(v,0) for v in x]+[(v,1) for v in y]);r1=ties=0;i=0
    while i<len(ordered):
        j=i+1
        while j<len(ordered) and ordered[j][0]==ordered[i][0]:j+=1
        r1+=((i+1+j)/2)*sum(t==0 for _,t in ordered[i:j]);ties+=(j-i)**3-(j-i);i=j
    u=r1-n*(n+1)/2;N=n+m;sigma=math.sqrt(n*m/12*((N+1)-ties/(N*(N-1))));z=(u-n*m/2)/sigma if sigma else 0
    return {'u':u,'z':round(z,3),'p_value':math.erfc(abs(z)/math.sqrt(2)),'rank_biserial_r':round(2*u/(n*m)-1,4)}

def group_stats(rows):
    result={'count':len(rows)}
    for f in ['word_count','internal_page_count']:result['median_'+f]=statistics.median(b[f] for b in rows) if rows else None
    for f in ['city_in_title_or_h1','city_in_h2','has_parseable_schema_type']:result['pct_'+f]=pct(sum(b[f] for b in rows),len(rows))
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input-dir',type=Path,default=Path(__file__).resolve().parent);ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args();src=args.input_dir;out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    runs=json.loads((src/'raw_1080_runs.json').read_text());config=json.loads((src/'study_config.json').read_text())
    overrides=json.loads((src/'manual_name_overrides.json').read_text())['runs'];snapshot=read_csv(src/'inspection_snapshot.csv')
    assert len({r['run_id'] for r in runs})==len(runs)==1080 and all(r['status']=='success' for r in runs)
    runs.sort(key=lambda r:int(r['run_id']));cells=defaultdict(list);pairs=defaultdict(list);sources=[];run_rows=[];names_rows=[]
    for r in runs:
        names=overrides.get(str(r['run_id']),extract_candidates(r['response_text']))
        if str(r['run_id']) in overrides:assert all(n in r['response_text'] for n in names),r['run_id']
        names=list({normalize_name(n):n for n in reversed(names)}.values())[::-1];r['names']=names;r['keys']=[normalize_name(n) for n in names]
        cells[(r['city'],r['category_id'])].append(r);pairs[(r['city'],r['category_id'],r['intent_id'])].append(r)
        for i,s in enumerate(r['sources']):
            d=source_domain(s);sources.append({'run_id':r['run_id'],'source_index':i,'city':r['city'],'category':r['category_id'],'source_title':s.get('title',''),'source_uri':s.get('uri',''),'resolved_domain':d,'source_class':source_class(d)})
        method='manual transcription' if str(r['run_id']) in overrides else 'bold-name candidate rules'
        run_rows.append({'run_id':r['run_id'],'city':r['city'],'category_id':r['category_id'],'intent_id':r['intent_id'],'paraphrase_index':r['paraphrase_index'],'prompt':r['prompt'],'search_query_count':len(r['search_queries_run']),'source_count':len(r['sources']),'name_count':len(names),'first_listed_name':names[0] if names else '','names_pipe':' | '.join(names),'search_queries_pipe':' | '.join(r['search_queries_run']),'extraction_method':method})
        for pos,name in enumerate(names,1):names_rows.append({'run_id':r['run_id'],'city':r['city'],'category':r['category_id'],'position':pos,'name':name,'canonical_name':normalize_name(name),'extraction_method':method})
    assert len(cells)==180 and all(len(v)==6 for v in cells.values())
    assert len(pairs)==540 and all(len(v)==2 for v in pairs.values())
    pair_rows=[]
    for key,rs in sorted(pairs.items()):
        a,b=sorted(rs,key=lambda r:r['paraphrase_index']);overlap=jaccard_similarity(a['names'],b['names']);comparable=bool(a['names'] and b['names'])
        pair_rows.append({'city':key[0],'category':key[1],'intent_id':key[2],'prompt_1':a['prompt'],'prompt_2':b['prompt'],'shortlist_1':' | '.join(a['names']),'shortlist_2':' | '.join(b['names']),'top_1_run_1':a['names'][0] if a['names'] else '','top_1_run_2':b['names'][0] if b['names'] else '','jaccard_overlap':overlap,'first_name_comparable':comparable,'same_top_1':bool(comparable and a['keys'][0]==b['keys'][0])})
    appearance=Counter()
    for rs in cells.values():appearance.update(Counter(k for r in rs for k in set(r['keys'])).values())
    seed_names={s['url'].split('://')[-1].split('/')[0].removeprefix('www.'):s['name'] for s in config['seed_businesses']}
    domains_by_cell=defaultdict(list)
    for b in snapshot:domains_by_cell[(b['city'],b['category'])].append(b)
    matched=defaultdict(set);first=defaultdict(set);matches=[]
    for cell,rs in sorted(cells.items()):
        for r in rs:
            for pos,name in enumerate(r['names'],1):
                candidates=[(b['domain'],reason) for b in domains_by_cell[cell] if (reason:=domain_match_reason(b['domain'],b['title'],name,seed_names.get(b['domain'],'')))]
                if len(candidates)==1:
                    d=candidates[0][0];matched[d].add(r['run_id'])
                    if pos==1:first[d].add(r['run_id'])
                matches.append({'run_id':r['run_id'],'city':cell[0],'category':cell[1],'name':name,'matched_domain':candidates[0][0] if len(candidates)==1 else '','match_reason':candidates[0][1] if len(candidates)==1 else ('ambiguous' if candidates else 'no conservative match'),'candidate_domains':' | '.join(d for d,_ in candidates)})
    business=[]
    for original in snapshot:
        b=dict(original);d=b['domain'];count=len(matched[d])
        for f in ['status_code','word_count','internal_page_count']:b[f]=int(b[f] or 0)
        for f in ['city_in_title_or_h1','city_in_h2','is_dead_or_parked']:b[f]=b[f]=='True'
        types=[t for t in b['schema_types'].split('|') if t and t!='Unparseable JSON-LD block']
        b['has_parseable_schema_type']=b['has_schema']=bool(types);b['runs_shortlisted_in']=count;b['runs_top1_in']=len(first[d]);b['inslr_percent']=pct(count,6)
        b['matching_scope']='original primary city/category; conservative automated identity';business.append(b)
    eligible=[b for b in business if b['status_code']==200 and not b['is_dead_or_parked']]
    leaders=[b for b in eligible if b['runs_shortlisted_in']>=3];unmatched=[b for b in eligible if b['runs_shortlisted_in']==0];occasional=[b for b in eligible if 1<=b['runs_shortlisted_in']<=2]
    fields=['city_in_title_or_h1','city_in_h2','has_parseable_schema_type']
    tests={f:proportion(sum(b[f] for b in leaders),len(leaders),sum(b[f] for b in unmatched),len(unmatched)) for f in fields}
    for f in ['word_count','internal_page_count']:tests[f]=mann_whitney([b[f] for b in leaders],[b[f] for b in unmatched])
    ordered=sorted(tests,key=lambda k:tests[k]['p_value']);adjusted=0
    for i,k in enumerate(ordered):adjusted=max(adjusted,min(1,(len(ordered)-i)*tests[k]['p_value']));tests[k]['p_holm_5_tests']=adjusted
    clusters=defaultdict(list)
    for b in leaders+unmatched:clusters[(b['city'],b['category'])].append(b)
    keys=sorted(clusters);rng=random.Random(40021);est={f:[] for f in fields}
    aggregates={k:(sum(b['runs_shortlisted_in']>=3 for b in clusters[k]),sum(b['runs_shortlisted_in']==0 for b in clusters[k]),[sum(b[f] for b in clusters[k] if b['runs_shortlisted_in']>=3) for f in fields],[sum(b[f] for b in clusters[k] if b['runs_shortlisted_in']==0) for f in fields]) for k in keys}
    for _ in range(2000):
        chosen=[aggregates[keys[rng.randrange(len(keys))]] for _ in keys];n=sum(v[0] for v in chosen);m=sum(v[1] for v in chosen)
        if not n or not m:continue
        for i,f in enumerate(fields):est[f].append(100*(sum(v[2][i] for v in chosen)/n-sum(v[3][i] for v in chosen)/m))
    for f,values in est.items():
        values.sort();tests[f]['cell_cluster_bootstrap_difference_95ci_pp']=[round(values[int(.025*len(values))],2),round(values[min(len(values)-1,int(.975*len(values)))],2)]
    counts=dict(sorted(Counter(s['source_class'] for s in sources).items()));overlaps=[p['jaccard_overlap'] for p in pair_rows if p['jaccard_overlap'] is not None];cp=[p for p in pair_rows if p['first_name_comparable']];same=sum(p['same_top_1'] for p in cp)
    summary={'analysis_version':'2.1','analysis_date':'2026-10-17','model':'gemini-2.5-flash','historical_temperature':'not explicitly set in archived harness','total_runs':len(runs),'paraphrase_pairs_tested':len(pair_rows),'total_subqueries_executed':sum(len(r['search_queries_run']) for r in runs),'total_grounding_sources':len(sources),'domain_resolved_sources':sum(v for k,v in counts.items() if k!='unresolved'),'source_class_counts':counts,'ownership_verified':False,'mean_paraphrase_jaccard_overlap_pct':round(statistics.mean(overlaps)*100,1),'median_paraphrase_jaccard_overlap_pct':round(statistics.median(overlaps)*100,1),'jaccard_defined_pairs':len(overlaps),'both_empty_pairs':len(pair_rows)-len(overlaps),'first_name_comparable_pairs':len(cp),'first_name_matches':same,'first_name_agreement_comparable_pct':pct(same,len(cp)),'first_name_agreement_all_pairs_pct':pct(same,len(pair_rows)),'total_unique_cell_business_appearances':sum(appearance.values()),'prompt_coverage_distribution':{str(k):{'count':appearance[k],'pct':pct(appearance[k],sum(appearance.values()))} for k in range(1,7)},'total_unique_business_domains_inspected':len(snapshot),'http_200_domains':sum(b['status_code']==200 for b in business),'eligible_http200_nonparked_domains':len(eligible),'tier_3_6_leaders_stats':group_stats(leaders),'tier_1_2_occasional_stats':group_stats(occasional),'tier_0_unmatched_stats':group_stats(unmatched),'statistical_tests':tests,'bootstrap':{'replicates':2000,'seed':40021,'unit':'original primary city-category cell'},'identity_match_counts':dict(sorted(Counter(x['match_reason'] for x in matches).items())),'raw_response_sha256':hashlib.sha256((src/'raw_1080_runs.json').read_bytes()).hexdigest(),'inspection_snapshot_sha256':hashlib.sha256((src/'inspection_snapshot.csv').read_bytes()).hexdigest()}
    for kind,field in [('city','city'),('category','category')]:
        result=[]
        for value in sorted({p[field] for p in pair_rows}):
            ps=[p for p in pair_rows if p[field]==value];ov=[p['jaccard_overlap'] for p in ps if p['jaccard_overlap'] is not None];cs=[p for p in ps if p['first_name_comparable']];rs=[r for r in runs if r['city' if kind=='city' else 'category_id']==value]
            result.append({field:value,'runs':len(rs),'pairs':len(ps),'mean_jaccard_overlap_pct':round(statistics.mean(ov)*100,1),'first_name_matches':sum(p['same_top_1'] for p in cs),'comparable_pairs':len(cs),'first_name_agreement_pct':pct(sum(p['same_top_1'] for p in cs),len(cs)),'grounding_sources':sum(len(r['sources']) for r in rs)})
        summary[kind+'_breakdown']=result
    for name,rows in [('runs_1080_summary.csv',run_rows),('paraphrase_pairs_540.csv',pair_rows),('businesses_inspected.csv',business),('extracted_names.csv',names_rows),('domain_name_matches.csv',matches),('grounding_sources.csv',sources)]:write_csv(out/name,rows)
    (out/'study_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['city_breakdown','category_breakdown','statistical_tests']},indent=2))
if __name__=='__main__':main()
