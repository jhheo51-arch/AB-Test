"""Preserve populated worksheet values in print without changing the blank form."""
PRINT_CSS='''<style>.record-print-value{display:none}@media print{.record-print-source{display:none!important}.record-print-value{display:block;white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;color:#142D32;background:#FFFFFF;border:1px solid #4F625F;padding:6px;min-height:15mm}.meta .record-print-value{min-height:8mm}.field:has(.record-print-value){break-inside:auto}.field:has(.record-print-value)>label,.field:has(.record-print-value)>small{break-after:avoid}}</style>'''
PRINT_JS=r'''<script>(()=>{
 function cleanup(){document.querySelectorAll('.record-print-value').forEach(e=>e.remove());document.querySelectorAll('.record-print-source').forEach(e=>e.classList.remove('record-print-source'))}
 window.addEventListener('beforeprint',()=>{cleanup();document.querySelectorAll('.meta input,.field textarea').forEach(e=>{if(!e.value.length)return;const text=document.createElement('div');text.className='record-print-value';text.textContent=e.value;e.after(text);e.classList.add('record-print-source')})});
 window.addEventListener('afterprint',cleanup);
})();</script>'''
