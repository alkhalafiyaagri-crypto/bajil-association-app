from pathlib import Path
import re

p=Path("bajil_android_project/app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")

# Exact login defaults.
s,n1=re.subn(r'(<input id="loginUser" value=")[^"]*(")',lambda m:m.group(1)+'نايف'+m.group(2),s,count=1)
s,n2=re.subn(r'(<input id="loginPass" type="password" value=")[^"]*(")',lambda m:m.group(1)+'123456'+m.group(2),s,count=1)
if n1!=1 or n2!=1: raise SystemExit("Login inputs not found")
s=s.replace('onclick="recoverDefaultLogin()"','onclick="recoverNaifLogin()"')
s=s.replace('onclick="recoverNaifLogin()"','onclick="recoverNaifLogin()"')
s=s.replace('الدخول الافتراضي: الخلفية / 1234','بيانات المدير: نايف / 123456')
s=s.replace('استعادة دخول المدير الافتراضي','استعادة حساب المدير نايف')

a=s.find("async function login(e){")
b=s.find("\nfunction logout()",a)
if a<0 or b<0: raise SystemExit("Could not locate login functions")

functions=r"""
async function persistLoginDatabase(){
 const snapshot=JSON.stringify(db);let saved=false,errors=[];
 try{localStorage.setItem(DBKEY,snapshot);saved=true}catch(e){errors.push('localStorage: '+(e.message||e))}
 try{
  const idb=await openLocalDB();
  await new Promise((resolve,reject)=>{
   const tx=idb.transaction('state','readwrite');
   tx.objectStore('state').put(snapshot,'database');
   tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error||Error('IndexedDB write failed'));tx.onabort=()=>reject(tx.error||Error('IndexedDB aborted'));
  });
  idb.close();saved=true;
 }catch(e){errors.push('IndexedDB: '+(e.message||e))}
 if(!saved)throw Error('تعذر حفظ بيانات الدخول محلياً. '+errors.join(' | '));
}
function setNaifAdminCredentials(){
 if(!Array.isArray(db.users))db.users=[];
 let user=db.users.find(x=>String(x.username||'').trim()==='نايف'&&x.role==='admin');
 if(!user)user=db.users.find(x=>x.role==='admin');
 if(!user)user=db.users.find(x=>String(x.username||'').trim()==='الخلفية'&&String(x.password||'')==='1234');
 if(!user){user={};db.users.push(user)}
 user.username='نايف';user.password='123456';user.role='admin';user.active=true;
 db.adminCredentialsVersion=1;
 return user;
}
async function login(e){
 if(e&&e.preventDefault)e.preventDefault();
 const btn=e&&e.submitter;if(btn)btn.disabled=true;$('loginError').style.display='none';
 try{
  if(window.__dbReady)await window.__dbReady;
  await load();
  if(db.adminCredentialsVersion!==1){setNaifAdminCredentials();await persistLoginDatabase();}
  const username=$('loginUser').value.trim(),password=$('loginPass').value;
  const user=db.users.find(x=>String(x.username||'').trim()===username&&String(x.password??'')===password&&x.active!==false);
  if(!user){$('loginError').textContent='بيانات الدخول غير صحيحة أو الحساب موقوف. بيانات المدير: نايف / 123456. استخدم استعادة حساب المدير إذا لزم الأمر.';$('loginError').style.display='block';return false}
  currentUser=user;$('login').style.display='none';$('app').style.display='block';
  $('welcome').textContent='المستخدم: '+username+' – '+roleName(user.role);applyPermissions();renderAll();return true;
 }catch(err){$('loginError').textContent='تعذر تجهيز قاعدة البيانات أو حفظ الحساب: '+(err&&err.message?err.message:'خطأ غير معروف');$('loginError').style.display='block';return false}
 finally{if(btn)btn.disabled=false}
}
async function recoverNaifLogin(){
 if(!confirm('سيتم ضبط حساب المدير إلى نايف / 123456. لن يتم حذف سجلات المزارعين أو المحاصيل أو المخزون أو السندات أو القيود. هل تريد المتابعة؟'))return;
 const btn=document.querySelector('#login button[onclick="recoverNaifLogin()"]');if(btn)btn.disabled=true;
 $('loginError').style.display='none';
 try{
  if(window.__dbReady)await window.__dbReady;
  await load();
  const admin=setNaifAdminCredentials();
  await persistLoginDatabase();
  $('loginUser').value='نايف';$('loginPass').value='123456';
  currentUser=admin;$('login').style.display='none';$('app').style.display='block';
  $('welcome').textContent='المستخدم: نايف – '+roleName(admin.role);applyPermissions();renderAll();
  alert('تم ضبط حساب المدير والدخول بنجاح. اسم المستخدم: نايف، كلمة المرور: 123456. سجلات الجمعية محفوظة.');
 }catch(err){$('loginError').textContent='تعذرت استعادة الحساب: '+(err&&err.message?err.message:'خطأ غير معروف');$('loginError').style.display='block';alert($('loginError').textContent)}
 finally{if(btn)btn.disabled=false}
}
"""
s=s[:a]+functions+s[b:]

# Replace either the prior asynchronous load marker or the original synchronous marker.
startup="""window.__dbReady=(async function(){
 await load();
 if(db.adminCredentialsVersion!==1){setNaifAdminCredentials();await persistLoginDatabase();}
 return true;
})().catch(function(e){console.warn('Initial database migration deferred to login',e);return false;});
"""
pat=r"(?:window\.__dbReady=load\(\);|load\(\);)\s*if\(\$\('reportYear'\)\)"
s,n=re.subn(pat,lambda m:startup+"if($('reportYear'))",s,count=1)
if n!=1: raise SystemExit("Could not locate application startup point")

assert 'id="loginUser" value="نايف"' in s
assert 'id="loginPass" type="password" value="123456"' in s
assert 'async function recoverNaifLogin()' in s
assert 'async function persistLoginDatabase()' in s
p.write_text(s,encoding="utf-8")
print("Naif login and one-time admin migration applied.")
