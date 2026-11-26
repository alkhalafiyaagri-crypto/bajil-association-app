from pathlib import Path
import re

p = Path("bajil_android_project/app/src/main/assets/index.html")
s = p.read_text(encoding="utf-8")

# Update the visible credentials and recovery action.
s, n1 = re.subn(r'(<input id="loginUser" value=")[^"]*(")', r'\1نايف\2', s, count=1)
s, n2 = re.subn(r'(<input id="loginPass" type="password" value=")[^"]*(")', lambda m: m.group(1)+''.join(chr(x) for x in (49,50,51,52,53,54))+m.group(2), s, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit("Could not safely update the login form defaults")
s = s.replace('onclick="recoverDefaultLogin()"', 'onclick="recoverNaifLogin()"')
s = s.replace('الدخول الافتراضي: الخلفية / 1234', 'بيانات المدير: نايف / 123456')
s = s.replace('استعادة دخول المدير الافتراضي', 'استعادة حساب المدير نايف')

# Replace login and recovery functions as one controlled block.
start = s.find("async function login(e){")
end = s.find("\nfunction logout()", start)
if start < 0 or end < 0:
    raise SystemExit("Login function boundary not found")

functions = r"""
async function persistLoginDatabase(){
 const snapshot=JSON.stringify(db);
 let saved=false, errors=[];
 try{localStorage.setItem(DBKEY,snapshot);saved=true}catch(e){errors.push('localStorage: '+(e.message||e))}
 try{
  const idb=await openLocalDB();
  await new Promise((resolve,reject)=>{
   const tx=idb.transaction('state','readwrite');
   tx.objectStore('state').put(snapshot,'database');
   tx.oncomplete=resolve;
   tx.onerror=()=>reject(tx.error||Error('IndexedDB write failed'));
   tx.onabort=()=>reject(tx.error||Error('IndexedDB transaction aborted'));
  });
  idb.close();saved=true;
 }catch(e){errors.push('IndexedDB: '+(e.message||e))}
 if(!saved)throw Error('تعذر حفظ بيانات الدخول محلياً. '+errors.join(' | '));
 return true;
}
function setNaifAdminCredentials(force){
 if(!Array.isArray(db.users))db.users=[];
 let target=db.users.find(u=>String(u.username||'').trim()==='نايف' && u.role==='admin');
 if(!target){
  target=db.users.find(u=>u.role==='admin');
  if(!target)target=db.users.find(u=>String(u.username||'').trim()==='الخلفية' && String(u.password||'')==='1234');
 }
 if(!target){
  target={username:'نايف',password:'123456',role:'admin',active:true};
  db.users.push(target);
 }else{
  target.username='نايف';
  target.password='123456';
  target.role='admin';
  target.active=true;
 }
 db.adminCredentialsVersion=1;
 return target;
}
async function login(e){
 if(e&&e.preventDefault)e.preventDefault();
 const btn=e&&e.submitter;if(btn)btn.disabled=true;
 $('loginError').style.display='none';
 try{
  await load();
  const u=$('loginUser').value.trim(),p=$('loginPass').value;
  let user=db.users.find(x=>String(x.username||'').trim()===u && String(x.password??'')===p && x.active!==false);
  if(!user){
   $('loginError').textContent='اسم المستخدم أو كلمة المرور غير صحيحين، أو أن الحساب موقوف. تأكد من كتابة نايف وكلمة المرور 123456، أو استخدم استعادة حساب المدير.';
   $('loginError').style.display='block';return false;
  }
  currentUser=user;
  $('login').style.display='none';$('app').style.display='block';
  $('welcome').textContent='المستخدم: '+u+' – '+roleName(user.role);
  applyPermissions();renderAll();return true;
 }catch(err){
  $('loginError').textContent='تعذر تجهيز قاعدة البيانات أو حفظ الدخول: '+(err&&err.message?err.message:'خطأ غير معروف');
  $('loginError').style.display='block';return false;
 }finally{if(btn)btn.disabled=false}
}
async function recoverNaifLogin(){
 if(!confirm('سيتم تغيير حساب المدير إلى نايف / 123456. ستبقى سجلات المزارعين والمحاصيل والمخزون والسندات والقيود كما هي. هل تريد المتابعة؟'))return;
 const btn=document.querySelector('#login button[onclick="recoverNaifLogin()"]');
 if(btn)btn.disabled=true;
 $('loginError').style.display='none';
 try{
  await load();
  const admin=setNaifAdminCredentials(true);
  await persistLoginDatabase();
  $('loginUser').value='نايف';$('loginPass').value='123456';
  currentUser=admin;
  $('login').style.display='none';$('app').style.display='block';
  $('welcome').textContent='المستخدم: نايف – '+roleName(admin.role);
  applyPermissions();renderAll();
  alert('تمت استعادة حساب المدير والدخول بنجاح. اسم المستخدم: نايف، كلمة المرور: 123456. لم يتم حذف سجلات الجمعية.');
 }catch(err){
  $('loginError').textContent='تعذرت استعادة الحساب: '+(err&&err.message?err.message:'خطأ غير معروف');
  $('loginError').style.display='block';
  alert($('loginError').textContent);
 }finally{if(btn)btn.disabled=false}
}
"""
s = s[:start] + functions + s[end:]

# On first startup only, migrate the previous default admin account to the requested credentials.
needle = "window.__dbReady=load();"
if needle not in s:
    raise SystemExit("Startup database initialization marker not found")
replacement = """window.__dbReady=(async function(){
 await load();
 if(db.adminCredentialsVersion!==1){
  setNaifAdminCredentials(false);
  await persistLoginDatabase();
 }
 return true;
})().catch(function(e){console.warn('Initial DB load deferred to login recovery',e);return false;});"""
s = s.replace(needle, replacement, 1)

p.write_text(s, encoding="utf-8")
print("Naif administrator login migration and recovery installed.")
