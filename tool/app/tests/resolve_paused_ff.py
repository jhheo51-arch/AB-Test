"""Resolve only paused merge text; preserve both published UI and R08 tooling."""
from pathlib import Path
import re,shutil,os
R=Path(__file__).resolve().parents[1];T=R.parent
if __name__=='__main__':
 backup=Path(os.environ['TMPDIR'])/'r08_paused_ff_backup';shutil.copytree(T,backup,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
 for relative,side in [('app/app.js',1),('app/tests/rebuild_package.py',2),('README.md',2),('downloads/README.md',2)]:
  path=T/relative;text=path.read_text('utf-8')
  text,n=re.subn(r'^<<<<<<<[^\n]*\n(.*?)^=======\n(.*?)^>>>>>>>[^\n]*\n?',lambda m:m.group(side),text,flags=re.M|re.S)
  assert n==1,(relative,n)
  path.write_text(text,encoding='utf-8');print('RESOLVED TEXT',relative)
