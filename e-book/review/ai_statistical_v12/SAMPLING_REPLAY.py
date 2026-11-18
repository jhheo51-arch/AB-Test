"""Replay recorded sampling cells with a separately written Pearson test."""
from pathlib import Path
import json,hashlib,platform
import numpy as np
from scipy.stats import chi2
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
p=ROOT/'e-book/virtual-data/v03/repeated_sampling_check.json';ledger=json.loads(p.read_text(encoding='utf-8'))
# Static specification inspection only: seed/cell order/A then B draws are stated
# in scripts/simulate_information_v03.py. That script is never imported/executed.
spec=ROOT/'scripts/simulate_information_v03.py';before={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [p,spec]}
rng=np.random.Generator(np.random.PCG64(ledger['seed']));pairs=[];checks=[]
for cell in ledger['results']:
 n=cell['n_per_arm'];reps=cell['replications'];pa=.09;pb=.09 if cell['scenario']=='no_effect' else .10
 a=rng.binomial(n,pa,size=reps);b=rng.binomial(n,pb,size=reps);pairs.append(np.stack([a,b]))
 # Pearson's 2x2 statistic equals the squared pooled-z statistic, but is
 # implemented here directly from total successes and the count difference.
 total=a+b;den=total*(2*n-total);pearson=np.divide(2*n*(b-a)**2,den,out=np.zeros(reps,dtype=float),where=den>0)
 rejects=int(np.count_nonzero(pearson>chi2.isf(ledger['alpha_each'],df=1)))
 checks.append({'n':n,'scenario':cell['scenario'],'replications':reps,'actual_rejections':rejects,'expected_rejections':cell['rejections'],'actual_rate':rejects/reps,'expected_rate':cell['observed_rejection_rate'],'status':'passed' if rejects==cell['rejections'] else 'mismatch'})
np.savez_compressed(OUT/'RECONSTRUCTED_SAMPLING_COUNTS.npz',counts=np.stack(pairs),seed=np.array(ledger['seed']))
for name,h in before.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
report={'kind':'Separate code deterministic replay of saved specification; not recovery of historical raw arrays','python':platform.python_version(),'numpy':np.__version__,'RNG':'PCG64 with recorded seed and source-declared draw/cell ordering','test':'Independently written Pearson statistic against chi-square(1) critical value, equivalent to two-sided pooled z','existing_generator_imported_or_executed':False,'seed_changed':False,'original_files_modified':False,'specification_hashes':before,'checks':checks,'summary':{'total':len(checks),'passed':sum(c['status']=='passed' for c in checks),'mismatch':sum(c['status']=='mismatch' for c in checks)},'reconstructed_counts_sha256':hashlib.sha256((OUT/'RECONSTRUCTED_SAMPLING_COUNTS.npz').read_bytes()).hexdigest(),'limits':['The original historical replication arrays were not retained/located; these arrays are explicitly newly reconstructed','Matching saved aggregates does not prove when the original run occurred or that a seed was fixed before results','This checks each single contrast, not joint three-arm FWER or field effectiveness']}
(OUT/'SAMPLING_REPLAY.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if not report['summary']['mismatch'] else 1)
