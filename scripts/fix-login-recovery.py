from pathlib import Path
import re

p = Path("bajil_android_project/app/src/main/assets/index.html")
s = p.read_text(encoding="utf-8")

# Add a safe account-recovery action without deleting association records.
form = re.search(r'(<form class="loginbox" onsubmit="login\(event\)">.*?</form>)', s, re.S)
if not form:
    raise SystemExit("Login form not found")
block = form.group(1)
if "recoverDefaultLogin" not in block:
    block = block.replace(
        '<button style="width:100%">تسجيل الدخول</button>',
        '<button type="submit" style="width:100%">تسجيل الدخول</button><button type="button" class="light" style="width:100%;margin-top:8px" onclick="recoverDefaultLogin()">استعادة دخول المدير الافتراضي</button>'
    )
    s = s[:form.start(1)] + block + s[form.end(1):]

# Normalize legacy accounts: missing active means enabled; explicit false remains disabled.
old = "if(!db.users.length)db.users=[{username:'الخلفية',password:'1234',role:'admin',active:true}]"
new = """db.users=(Array.isArray(db.users)?db.users:[]).map(u=>({...u,username:String(u.username??'').trim(),password:String(u.password??''),role:u.role||'staff',active:u.active===false||u.active==='false'?false:true}));if(!db.users.length)db.users=[{username:'الخلفية',password:'1234',role:'admin',active:true}]"""
if old not in s:
    raise SystemExit("Expected user initialization code not found")
s = s.replace(old, new, 1)

# Await the initial database load before accepting credentials.
s = s.replace(
    "async function login(e){e.preventDefault();let btn=e.submitter;if(btn)btn.disabled=true;try{await load();let u=$('loginUser').value.trim(),p=$('loginPass').value,user=db.users.find(x=>x.username===u&&x.password===p&&x.active);if(!user){$('loginError').style.display='block';return}currentUser=user;$('login').style.display='none';$('app').style.display='block';$('welcome').textContent='المستخدم: '+u+' – '+roleName(user.role);applyPermissions();renderAll()}finally{if(btn)btn.disabled=false}}",
    """async function login(e){e.preventDefault();let btn=e.submitter;if(btn)btn.disabled=true;$('loginError').style.display='none';try{await (window.__dbReady||load());let u=$('loginUser').value.trim(),p=$('loginPass').value,user=db.users.find(x=>String(x.username||'').trim()===u&&String(x.password??'')===p&&x.active!==false);if(!user){$('loginError').textContent='بيانات الدخول غير مطابقة للحساب المحفوظ أو أن الحساب موقوف. استخدم استعادة دخول المدير إذا كنت مالك الجهاز.';$('loginError').style.display='block';return}currentUser=user;$('login').style.display='none';$('app').style.display='block';$('welcome').textContent='المستخدم: '+u+' – '+roleName(user.role);applyPermissions();renderAll()}catch(err){$('loginError').textContent='تعذر تجهيز قاعدة البيانات: '+(err.message||'خطأ غير معروف');$('loginError').style.display='block'}finally{if(btn)btn.disabled=false}}"""
)

anchor = "function logout(){"
recovery = """async function recoverDefaultLogin(){if(!confirm('سيتم إعادة حساب المدير إلى: الخلفية / 1234. لن يتم حذف المزارعين أو الحسابات أو السندات أو أي سجلات أخرى. هل تريد المتابعة؟'))return;try{await (window.__dbReady||load());db.users=[{username:'الخلفية',password:'1234',role:'admin',active:true}];let snapshot=JSON.stringify(db);localStorage.setItem(DBKEY,snapshot);try{let idb=await openLocalDB();await new Promise((resolve,reject)=>{let tx=idb.transaction('state','readwrite');tx.objectStore('state').put(snapshot,'database');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});idb.close()}catch(storageError){if(!localStorage.getItem(DBKEY))throw storageError} $('loginUser').value='الخلفية';$('loginPass').value='1234';$('loginError').style.display='none';alert('تمت استعادة حساب المدير. اسم المستخدم: الخلفية، كلمة المرور: 1234. سجلات الجمعية محفوظة. يمكنك الآن تسجيل الدخول.')}catch(err){alert('تعذرت استعادة الدخول: '+(err.message||''))}}
"""
if "async function recoverDefaultLogin()" not in s:
    if anchor not in s:
        raise SystemExit("Logout function anchor not found")
    s = s.replace(anchor, recovery + anchor, 1)

old_init = "load(); if($('reportYear'))$('reportYear').value=new Date().getFullYear();"
new_init = "window.__dbReady=load(); if($('reportYear'))$('reportYear').value=new Date().getFullYear();"
if old_init not in s:
    raise SystemExit("Initial database load call not found")
s = s.replace(old_init, new_init, 1)

p.write_text(s, encoding="utf-8")
print("Login recovery patch applied; association records are preserved.")
