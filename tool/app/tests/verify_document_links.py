"""Check every Markdown local link (including glob targets) in a supplied tree."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
import argparse,json,re,glob

def check_links(root):
 root=Path(root).resolve();rows=[];docs=sorted(root.rglob('*.md'))
 for doc in docs:
  text=doc.read_text(encoding='utf-8-sig')
  refs=re.findall(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)',text)
  refs+=re.findall(r'^\s*\[[^\]]+\]:\s*(\S+)',text,re.M)
  for ref in refs:
   ref=ref.strip('<>');split=urlsplit(ref)
   if split.scheme or split.netloc or not split.path:continue
   path=unquote(split.path);target=(doc.parent/path).resolve()
   exists=bool(glob.glob(str(target),recursive=True)) if any(c in path for c in '*?[') else target.exists()
   rows.append({'source':doc.relative_to(root).as_posix(),'reference':ref,'target':str(target),'exists':exists})
 return {'status':'PASS' if all(r['exists'] for r in rows) else 'FAIL','markdown_documents':len(docs),'local_links_checked':len(rows),'broken_links':[r for r in rows if not r['exists']],'links':rows,'scope':'all Markdown local path links, reference links and glob targets; URLs/anchor semantics not verified'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--output',required=True);args=a.parse_args();r=check_links(args.root);Path(args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='links'},ensure_ascii=False));raise SystemExit(0 if r['status']=='PASS' else 1)
