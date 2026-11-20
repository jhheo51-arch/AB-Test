"""Read-only source audit. No model, credentials, app writes, or network."""
from pathlib import Path
import ast, hashlib, json, re, subprocess
BASE=Path('C:/Users/Administrator/Downloads/AB_Test_Workspace_v04')
OUT=Path('C:/Users/Administrator/Downloads/AB_Test_Workspace_v04_Audit/static')
names=['app.js','server.py','narrative.js','engine.js','index.html','INPUT_DECISION_CONTRACT.md','DECISION_CONTEXT_CONTRACT_v04.md']
before={n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in names}
js=r'''
const fs=require('fs'),vm=require('vm');
const base=process.argv[1]; const nodes={};
function node(s){return nodes[s]??=( {value:'',checked:false,disabled:false,hidden:false,innerHTML:'',textContent:'',className:'',addEventListener(){}});}
const ctx={console,TextEncoder,TextDecoder,Set,Map,Number,String,JSON,Array,Object,Error,Boolean,crypto:require('crypto').webcrypto,ABNarrative:require(base+'/narrative.js'),document:{querySelector:node,querySelectorAll:()=>[]},window:{scrollTo(){}},clearTimeout(){},setTimeout(){}};
vm.createContext(ctx);
const app=fs.readFileSync(base+'/app.js','utf8').split("document.addEventListener('click'")[0]; vm.runInContext(app,ctx);
const engine=require(base+'/engine.js');const plan={randomized:true,independent:true,mature:true,fixedStop:true,includeSegments:true,segmentPrespecified:true,alpha:.05};
const csv='arm,success,total,segment\nA,10,100,PRIVATE_GROUP_ALPHA\nB,20,100,PRIVATE_GROUP_ALPHA\nA,20,100,PRIVATE_GROUP_BETA\nB,10,100,PRIVATE_GROUP_BETA';
ctx.p=engine.prepare(csv,'aggregate');ctx.r=engine.analyze(ctx.p,plan);
vm.runInContext("state.prepared=p;state.result=r;state.sourceKind='pasted';",ctx);
for(const id of ['purpose','metric','window','policy-a','policy-b','audience','decision','revisit'])node('#'+id).value='FREE_TEXT_SENTINEL_'+id;
for(const id of ['randomized','independent','mature','fixed-stop','include-segments','segment-prespecified'])node('#'+id).checked=true;
const facts=vm.runInContext('explanationFacts()',ctx);
node('#share-groups').checked=false;const hidden=vm.runInContext('reportHTML()',ctx);
node('#share-groups').checked=true;const visible=vm.runInContext('reportHTML()',ctx);
node('#share-groups').checked=false;node('#audience').value='<img src=x onerror=alert(1)> PRIVATE_GROUP_ALPHA';const escaped=vm.runInContext('reportHTML()',ctx);
async function roundtrip(cells){ctx.cells=cells;vm.runInContext('state.prepared={cells,issues:[]};state.result=null;',ctx); const saved=vm.runInContext('projectObject()',ctx);ctx.file={size:Buffer.byteLength(JSON.stringify(saved)),text:async()=>JSON.stringify(saved)};await vm.runInContext('restoreProject(file)',ctx);return {saved_cells:saved.cells.length,saved_bytes:ctx.file.size,toast:node('#toast').textContent};}
(async()=>{
node('#audience').value='normal';
const longSegment=engine.prepare('arm,success,total,segment\nA,1,10,'+'S'.repeat(201)+'\nB,2,10,'+'S'.repeat(201),'aggregate');
const many=engine.prepare('arm,success,total,segment\n'+Array.from({length:7},(_,i)=>['A,1,10,G'+i,'B,2,10,G'+i].join('\n')).join('\n'),'aggregate');
const largeCount=engine.prepare('arm,success,total\nA,1,200001\nB,2,200001','aggregate');
console.log(JSON.stringify({facts,model_payload_has_free_text:JSON.stringify(facts).includes('FREE_TEXT_SENTINEL'),model_payload_has_original_group:JSON.stringify(facts).includes('PRIVATE_GROUP'),excluded:{has_private_names:hidden.includes('PRIVATE_GROUP'),has_group_reason:hidden.includes('data-reason="INTERACTION_'),has_group_pvalue:hidden.includes(String(ctx.r.segments[0].p_raw)),has_family_keys:hidden.includes('G1')&&hidden.includes('G2'),has_free_text:hidden.includes('FREE_TEXT_SENTINEL'),included_report_has_private_names:visible.includes('PRIVATE_GROUP')},escaping:{literal_markup:escaped.includes('<img src=x'),escaped_markup:escaped.includes('&lt;img src=x'),user_group_text_preserved:escaped.includes('PRIVATE_GROUP_ALPHA')},roundtrip:[{case:'segment_201_char',prepare_errors:longSegment.issues.filter(i=>i.severity==='error'),result:await roundtrip(longSegment.cells)},{case:'seven_segments_fourteen_cells',prepare_errors:many.issues.filter(i=>i.severity==='error'),result:await roundtrip(many.cells)},{case:'per_arm_200001',prepare_errors:largeCount.issues.filter(i=>i.severity==='error'),result:await roundtrip(largeCount.cells)}]},null,2));
})().catch(e=>{console.error(e.stack);process.exit(1)});
'''
run=subprocess.run(['node','-e',js,str(BASE)],capture_output=True,text=True,encoding='utf-8',timeout=30)
if run.returncode:raise RuntimeError(run.stderr)
node_results=json.loads(run.stdout)
# Compile only the pure validator, never import/execute server or CLI setup.
tree=ast.parse((BASE/'server.py').read_text(encoding='utf-8'))
func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_facts')
ns={'re':re,'STATUSES':{'valid','limited','invalid','unsupported'},'DECISIONS':{'A','B','hold','not_tested'}}
exec(compile(ast.Module(body=[func],type_ignores=[]),'<isolated validator>','exec'),ns)
facts=node_results['facts']; rejected={}
for key in ['audience','policyA','purpose','raw_csv']:
    candidate={**facts,key:'SYNTHETIC_SENTINEL'}
    try:ns['validate_facts'](candidate);rejected[key]=False
    except ValueError:rejected[key]=True
candidate={**facts,'issues':['EMAIL_ALICE_EXAMPLE_COM','CUSTOMER_01012345678']}
accepted=ns['validate_facts'](candidate)==candidate
after={n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in names}
result={'scope':'read-only isolated pure-function/file tests; no HTTP/model/credential access','node':node_results,'server_validator':{'extra_free_text_keys_rejected':rejected,'arbitrary_identifier_shaped_issue_strings_accepted':accepted,'sentinel_issues':candidate['issues']},'source_sha256_before':before,'source_sha256_after':after,'all_read_sources_unchanged':before==after,'limitations':['No browser end-to-end execution','No actual Hermes/LLM request','No claim about real provider payload or CLI-added context','Only named source files hashed, not a complete workspace snapshot']}
(OUT/'privacy_contract_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
