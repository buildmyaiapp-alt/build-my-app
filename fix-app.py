#!/usr/bin/env python3
"""
Fix My App — Button Fixer
Run:  python3 fix-app.py my-app.html
Output: my-app-FIXED.html  (in the same folder)
"""
import re, sys, os

def repair(html):
    def fix_script(m):
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)

        # FIX 1: standalone function declarations
        body = re.sub(
            r'^(\s*)(async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(',
            lambda m: m.group(1)+'var '+m.group(3)+' = window.'+m.group(3)+' = '+(m.group(2) or '')+'function '+m.group(3)+'(',
            body, flags=re.MULTILINE)

        # FIX 1b: const/let X = [async] function(
        body = re.sub(
            r'^(\s*)(?:const|let)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(async\s+)?function\s*(?:[A-Za-z_$][A-Za-z0-9_$]*)?\s*\(',
            lambda m: m.group(1)+'var '+m.group(2)+' = window.'+m.group(2)+' = '+(m.group(3) or '')+'function '+m.group(2)+'(',
            body, flags=re.MULTILINE)

        # FIX 1c: const/let X = [async] (params) =>
        body = re.sub(
            r'^(\s*)(?:const|let)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(async\s+)?\(([^)]*)\)\s*=>',
            lambda m: m.group(1)+'var '+m.group(2)+' = window.'+m.group(2)+' = '+(m.group(3) or '')+'('+m.group(4)+') =>',
            body, flags=re.MULTILINE)

        # FIX 1d: const/let X = async? singleParam =>
        body = re.sub(
            r'^(\s*)(?:const|let)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(async\s+)?([A-Za-z_$][A-Za-z0-9_$]*)\s*=>',
            lambda m: m.group(1)+'var '+m.group(2)+' = window.'+m.group(2)+' = '+(m.group(3) or '')+m.group(4)+' =>',
            body, flags=re.MULTILINE)

        # FIX 3: DOMContentLoaded / load → __runWhenReady
        body = re.sub(r"document\.addEventListener\s*\(\s*['\"]DOMContentLoaded['\"]\s*,\s*", '__runWhenReady(', body)
        body = re.sub(r"window\.addEventListener\s*\(\s*['\"]load['\"]\s*,\s*", '__runWhenReady(', body)
        body = re.sub(r"window\.onload\s*=\s*function\s*", '__runWhenReady(function ', body)

        # Inject helpers if not already present
        if '__runWhenReady' not in body:
            ready   = 'function __runWhenReady(fn){if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",fn);}else{fn();}}'
            err_def = 'if(!window._showBtnErr){window._showBtnErr=function(msg){try{var _t=document.createElement("div");_t.textContent="⚠️ "+msg;_t.style.cssText="position:fixed;top:12px;left:50%;transform:translateX(-50%);background:#c62828;color:#fff;padding:10px 18px;border-radius:10px;z-index:99999;font-size:13px;max-width:90%;text-align:center;cursor:pointer;";_t.onclick=function(){_t.remove();};document.body.appendChild(_t);setTimeout(function(){if(_t.parentNode)_t.remove();},8000);}catch(e){}};}'
            onerr   = 'window.onerror=function(msg,s,l,c,err){if(window._showBtnErr)window._showBtnErr((err&&err.message)||msg);return false;};window.addEventListener("unhandledrejection",function(ev){if(window._showBtnErr)window._showBtnErr("Promise: "+((ev.reason&&ev.reason.message)||ev.reason||"?"));});'
            body    = ready + '\n' + err_def + '\n' + onerr + '\n' + body

        # FIX 2: onclick rebinder using new Function (global scope)
        err   = 'if(!window._showBtnErr){window._showBtnErr=function(msg){try{var _t=document.createElement("div");_t.textContent="⚠️ "+msg;_t.style.cssText="position:fixed;top:12px;left:50%;transform:translateX(-50%);background:#c62828;color:#fff;padding:10px 18px;border-radius:10px;z-index:99999;font-size:13px;max-width:90%;text-align:center;cursor:pointer;";_t.onclick=function(){_t.remove();};document.body.appendChild(_t);setTimeout(function(){if(_t.parentNode)_t.remove();},8000);}catch(e){}};}'
        rebind = err+'try{document.querySelectorAll("[onclick]").forEach(function(el){if(el._ocDone)return;el._ocDone=true;var oc=el.getAttribute("onclick");el.removeAttribute("onclick");el.addEventListener("click",function(e){try{(new Function("event",oc)).call(el,e);}catch(ex){if(window._showBtnErr)window._showBtnErr(ex.message+" ["+oc.slice(0,40)+"]");console.error("btn-fail:",oc,ex);}});});}catch(_e){console.error("evalRebind",_e);}'
        obs    = 'try{if(!window._moSetup){window._moSetup=true;var _rw=function(){try{document.querySelectorAll("[onclick]").forEach(function(el){if(el._ocDone)return;el._ocDone=true;var oc=el.getAttribute("onclick");el.removeAttribute("onclick");el.addEventListener("click",function(e){try{(new Function("event",oc)).call(el,e);}catch(ex){if(window._showBtnErr)window._showBtnErr(ex.message+" ["+oc.slice(0,40)+"]");console.error("btn-fail:",oc,ex);}});});}catch(e){}};if(document.body)new MutationObserver(function(){setTimeout(_rw,30);}).observe(document.body,{childList:true,subtree:true});var _ri=0;var _rint=setInterval(function(){_rw();if(++_ri>60)clearInterval(_rint);},500);}}catch(_me){console.error("obs",_me);}'

        body += '\n'+obs
        body += '\nsetTimeout(function(){'+rebind+'\n'+obs+'},300);'
        body += '\nsetTimeout(function(){'+rebind+'},1500);'
        body += '\nsetTimeout(function(){'+rebind+'},4000);'

        return open_tag + body + '\n' + close_tag

    return re.sub(r'(<script(?!\s+src)[^>]*>)([\s\S]*?)(</script>)', fix_script, html, flags=re.IGNORECASE)

# ── Main ──────────────────────────────────────────────────────────
src = sys.argv[1] if len(sys.argv) > 1 else 'my-app.html'

if not os.path.exists(src):
    print('❌  File not found:', src)
    print('    Usage:  python3 fix-app.py my-app.html')
    sys.exit(1)

with open(src, 'r', encoding='utf-8', errors='replace') as f:
    html = f.read()

fixed = repair(html)

base, ext = os.path.splitext(src)
out = base + '-FIXED' + ext

with open(out, 'w', encoding='utf-8') as f:
    f.write(fixed)

print('✅  Fixed!  →  ' + out)
print('    Open that file in your browser.')
