#!/usr/bin/env python3
"""Regression checks plus three full offline hash-seed replays of Report 004."""
import csv, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
from analysis_core import extract_candidates, normalize_name, jaccard_similarity, domain_match_reason
ROOT=Path(__file__).resolve().parent

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def check():
    raw=json.loads((ROOT/'raw_1080_runs.json').read_text());runs={str(r['run_id']):r for r in raw}
    names=extract_candidates(runs['67']['response_text'])
    assert names[0]=='Dismuke Insurance Agency'
    assert 'Jennifer Robinette Insurance Agency' in names and 'Smith & Sons Insurance Agency' in names
    assert 'Approach' not in extract_candidates(runs['37']['response_text'])
    assert 'Contact' not in extract_candidates(runs['37']['response_text'])
    assert normalize_name('Consider It Fixed Auto Repair')=='consider it fixed auto repair'
    assert len(extract_candidates(runs['67']['response_text']))>10
    assert normalize_name('Comfort Solutions')=='comfort solutions'
    assert normalize_name('ACME, LLC')==normalize_name('ACME')
    assert normalize_name('ACME Tulsa')!=normalize_name('ACME Lawton')
    assert jaccard_similarity(['A','B'],['B','C'])==1/3
    assert jaccard_similarity([],[]) is None
    assert jaccard_similarity(['Comfort Air'],['Comfort Plumbing'])==0
    assert not domain_match_reason('comfortplumbing.com','Comfort Plumbing','Comfort Air')
    assert domain_match_reason('webbbranding.com','WEBB Branding','WEBB Branding')
    before={n:digest(ROOT/n) for n in ['raw_1080_runs.json','inspection_snapshot.csv']}
    outputs=['runs_1080_summary.csv','paraphrase_pairs_540.csv','businesses_inspected.csv','extracted_names.csv','domain_name_matches.csv','grounding_sources.csv','study_summary.json']
    expected={n:digest(ROOT/n) for n in outputs}
    with tempfile.TemporaryDirectory(prefix='report004-verify-') as tmp:
        for seed in ['1','2','8675309']:
            dest=Path(tmp)/seed
            env=os.environ.copy();env['PYTHONHASHSEED']=seed
            # Remove API credential variables: reproduction must not depend on them.
            for key in list(env):
                if any(t in key for t in ['API_KEY','SECRET','TOKEN']):env.pop(key)
            subprocess.run([sys.executable,str(ROOT/'study_analyzer.py'),'--input-dir',str(ROOT),'--output-dir',str(dest)],env=env,stdout=subprocess.DEVNULL,check=True)
            assert {n:digest(dest/n) for n in outputs}==expected,seed
            figures=dest/'figures'
            subprocess.run([sys.executable,str(ROOT/'generate_figures.py'),'--data-dir',str(dest),'--output-dir',str(figures)],env=env,stdout=subprocess.DEVNULL,check=True)
            assert {p.name:digest(p) for p in figures.glob('*.svg')}=={p.name:digest(p) for p in (ROOT/'figures').glob('*.svg')},seed
            print('Full offline replay and figures match published outputs; hash seed',seed)
    assert {n:digest(ROOT/n) for n in before}==before
    pairs=list(csv.DictReader((ROOT/'paraphrase_pairs_540.csv').open()))
    summary=json.loads((ROOT/'study_summary.json').read_text())
    assert len(pairs)==540 and sum(p['same_top_1']=='True' for p in pairs)==summary['first_name_matches']
    assert sum(v['count'] for v in summary['prompt_coverage_distribution'].values())==summary['total_unique_cell_business_appearances']
    assert sum(summary['source_class_counts'].values())==8370
    print('Insurance/name regressions, metric denominators and immutable inputs verified.')
if __name__=='__main__':check()
