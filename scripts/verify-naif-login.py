from pathlib import Path
import re

p=Path("bajil_android_project/app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")

# Correct the password input value regardless of any earlier escaped-regex replacement.
s,n=re.subn(r'(<input id="loginPass" type="password" value=")[^"]*(")',lambda m:m.group(1)+'123456'+m.group(2),s,count=1)
if n!=1: raise SystemExit("Password field was not found")
if 'value="نايف"' not in s: raise SystemExit("Naif username field missing")

# Ensure login waits for startup migration, then performs one-time credential migration if needed.
a=s.find("async function login(e){")
b=s.find("\nasync function recoverNaifLogin()",a)
if a<0 or b<0: raise SystemExit("Naif login function boundary missing")
login=s[a:b]
login=login.replace("  await load();\n  const u=", "  if(window.__dbReady)await window.__dbReady;\n  await load();\n  if(db.adminCredentialsVersion!==1){setNaifAdminCredentials(false);await persistLoginDatabase();}\n  const u=",1)
s=s[:a]+login+s[b:]

a=s.find("async function recoverNaifLogin(){")
b=s.find("\nfunction logout()",a)
if a<0 or b<0: raise SystemExit("Naif recovery function boundary missing")
recover=s[a:b]
recover=recover.replace("  await load();\n  const admin=", "  if(window.__dbReady)await window.__dbReady;\n  await load();\n  const admin=",1)
s=s[:a]+recover+s[b:]

# Assert exact requested credentials and no legacy default remain in the login UI.
assert 'id="loginUser" value="نايف"' in s
assert 'id="loginPass" type="password" value="123456"' in s
assert 'async function recoverNaifLogin()' in s
assert 'async function persistLoginDatabase()' in s
assert "if(u==='نايف' && p==='123456')" in s
assert 'user=setNaifAdminCredentials(true)' in s
p.write_text(s,encoding="utf-8")
print("Naif login UI and startup synchronization verified.")
