from pathlib import Path
p=Path('bajil_android_project/app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'async function load(){' not in s: raise SystemExit('load not found')
s=s.replace('async function load(){','async function load(){',1)
p.write_text(s,encoding='utf-8')
