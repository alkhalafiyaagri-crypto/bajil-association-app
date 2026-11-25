from pathlib import Path
import re

root = Path("bajil_android_project")
html = root / "app/src/main/assets/index.html"
s = html.read_text(encoding="utf-8")

# Exact farmer form order. The existing farmer ID remains hidden and is never regenerated for old records.
m = re.search(r'<section id="farmers" class="panel active">.*?</section>', s, re.S)
assert m, "Farmers section not found"
section = """<section id="farmers" class="panel active"><h2>إدارة المزارعين</h2><div class="formbox"><form id="farmerForm"><input type="hidden" name="id"><input type="hidden" name="oldId"><div class="grid">
<div class="field"><label>اسم المزارع *</label><input name="name" required></div>
<div class="field"><label>نوع البطاقة</label><select name="cardType"><option value="">بدون بطاقة</option><option>بطاقة شخصية</option><option>بطاقة عائلية</option><option>بطاقة انتخابية</option><option>جواز سفر</option><option>بطاقة أخرى</option></select></div>
<div class="field"><label>رقم البطاقة</label><input name="cardNumber" autocomplete="off" placeholder="أدخل رقم البطاقة"></div>
<div class="field"><label>القرية / المحل</label><input name="village"></div>
<div class="field"><label>العزلة</label><input name="isolation"></div>
<div class="field"><label>المديرية</label><input name="directorate" value="باجل"></div>
<div class="field"><label>المحافظة</label><input name="governorate" value="الحديدة"></div>
<div class="field"><label>الانتساب</label><select name="membership"><option>منتسب للجمعية</option><option>غير منتسب للجمعية</option></select></div>
<div class="field"><label>رقم الهاتف</label><input name="phone" inputmode="tel"></div>
<div class="field"><label>الملاحظات</label><input name="notes"></div>
</div><div class="buttons"><button>حفظ المزارع</button><button type="button" class="light" onclick="resetForm('farmerForm')">تفريغ الحقول</button></div><p class="muted">رقم العضوية محفوظ داخلياً لضمان استمرار ارتباط السندات والقيود والسجلات السابقة.</p></form></div><input class="search" placeholder="بحث بالاسم أو العضوية أو القرية أو العزلة" oninput="renderFarmers(this.value)"><div class="tablewrap"><table><thead><tr><th>المعرّف</th><th>اسم المزارع</th><th>نوع البطاقة</th><th>رقم البطاقة</th><th>القرية / المحل</th><th>العزلة</th><th>المديرية</th><th>المحافظة</th><th>الانتساب</th><th>الهاتف</th><th>الملاحظات</th><th>الإجراءات</th></tr></thead><tbody id="farmerRows"></tbody></table></div></section>"""
s = s[:m.start()] + section + s[m.end():]
s = s.replace('type="file" accept="image/*"', 'type="file" accept="image/*" capture="environment"')

old_load = """function load(){try{let raw=localStorage.getItem(DBKEY)||localStorage.getItem(OLDKEY);let d=raw?JSON.parse(raw):null;if(d)db={...db,...d,counters:{receipt:0,payment:0,...d.counters},journal:d.journal||[],cashOps:d.cashOps||[]};}catch(e){alert('تعذرت قراءة قاعدة البيانات المحلية')};db.farmers=db.farmers.map(f=>({...f,cardType:f.cardType||'',cardNumber:f.cardNumber||''}));if(!db.users.length)db.users=[{username:'الخلفية',password:'1234',role:'admin',active:true}]}
function save(){try{localStorage.setItem(DBKEY,JSON.stringify(db));renderAll()}catch(e){alert('مساحة التخزين غير كافية. نزّل نسخة احتياطية واحذف الملفات/البيانات غير اللازمة.')}}"""
new_load = """function openLocalDB(){return new Promise((resolve,reject)=>{if(!window.indexedDB)return reject(Error('IndexedDB unavailable'));let req=indexedDB.open('BajilAssociationStore',1);req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains('state'))req.result.createObjectStore('state')};req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error)})}
async function readStoredState(){try{let idb=await openLocalDB();let value=await new Promise((resolve,reject)=>{let tx=idb.transaction('state','readonly'),r=tx.objectStore('state').get('database');r.onsuccess=()=>resolve(r.result||null);r.onerror=()=>reject(r.error)});idb.close();if(value)return JSON.parse(value)}catch(e){}let raw=localStorage.getItem(DBKEY)||localStorage.getItem(OLDKEY);return raw?JSON.parse(raw):null}
async function load(){try{let d=await readStoredState();if(d)db={...db,...d,counters:{receipt:0,payment:0,...d.counters},journal:d.journal||[],cashOps:d.cashOps||[]}}catch(e){alert('تعذرت قراءة قاعدة البيانات المحلية: '+(e.message||''))}db.farmers=db.farmers.map(f=>({...f,cardType:f.cardType||'',cardNumber:f.cardNumber||'',village:f.village||'',isolation:f.isolation||'',directorate:f.directorate||'باجل',governorate:f.governorate||'الحديدة',membership:f.membership||'غير منتسب للجمعية',phone:f.phone||'',notes:f.notes||''}));if(!db.users.length)db.users=[{username:'الخلفية',password:'1234',role:'admin',active:true}]}
function save(){renderAll();let snapshot=JSON.stringify(db);try{localStorage.setItem(DBKEY,snapshot)}catch(e){}openLocalDB().then(idb=>new Promise((resolve,reject)=>{let tx=idb.transaction('state','readwrite');tx.objectStore('state').put(snapshot,'database');tx.oncomplete=()=>{idb.close();resolve()};tx.onerror=()=>{idb.close();reject(tx.error)}})).catch(e=>alert('تعذر حفظ البيانات محلياً. صدّر نسخة احتياطية فوراً. '+(e.message||'')))}"""
assert old_load in s, "Original local persistence code changed; aborting"
s = s.replace(old_load, new_load)
old_login = "function login(e){e.preventDefault();load();let u=$('loginUser').value.trim(),p=$('loginPass').value,user=db.users.find(x=>x.username===u&&x.password===p&&x.active);if(!user){$('loginError').style.display='block';return}currentUser=user;$('login').style.display='none';$('app').style.display='block';$('welcome').textContent='المستخدم: '+u+' – '+roleName(user.role);applyPermissions();renderAll()}"
new_login = "async function login(e){e.preventDefault();let btn=e.submitter;if(btn)btn.disabled=true;try{await load();let u=$('loginUser').value.trim(),p=$('loginPass').value,user=db.users.find(x=>x.username===u&&x.password===p&&x.active);if(!user){$('loginError').style.display='block';return}currentUser=user;$('login').style.display='none';$('app').style.display='block';$('welcome').textContent='المستخدم: '+u+' – '+roleName(user.role);applyPermissions();renderAll()}finally{if(btn)btn.disabled=false}}"
assert old_login in s
s = s.replace(old_login, new_login)

# Replace the single-line renderer without changing farmer IDs or relational lookups.
lines = s.splitlines()
for i, line in enumerate(lines):
    if line.startswith("function renderFarmers(q="):
        lines[i] = """function renderFarmers(q=''){let term=String(q||'').trim();$('farmerRows').innerHTML=db.farmers.filter(x=>[x.id,x.name,x.cardType,x.cardNumber,x.village,x.isolation,x.directorate,x.governorate,x.membership,x.phone,x.notes].join(' ').includes(term)).map(x=>'<tr><td>'+esc(x.id)+'</td><td>'+esc(x.name)+'</td><td>'+esc(x.cardType||'')+'</td><td>'+esc(x.cardNumber||'')+'</td><td>'+esc(x.village||'')+'</td><td>'+esc(x.isolation||'')+'</td><td>'+esc(x.directorate||'')+'</td><td>'+esc(x.governorate||'')+'</td><td>'+esc(x.membership||'')+'</td><td>'+esc(x.phone||'')+'</td><td>'+esc(x.notes||'')+'</td><td><button class="small" data-id="'+esc(x.id)+'" onclick="editFarmer(this.dataset.id)">تعديل</button> <button class="small light" data-id="'+esc(x.id)+'" onclick="farmerStatement(this.dataset.id)">كشف</button> <button class="small danger" data-id="'+esc(x.id)+'" data-table="farmers" data-key="id" onclick="del(this.dataset.table,this.dataset.id,this.dataset.key)">حذف</button></td></tr>').join('')}"""
        break
else:
    raise SystemExit("Farmer renderer not found")
s = "\n".join(lines) + "\n"

old_submit = "$('farmerForm').onsubmit=e=>{e.preventDefault();if(currentUser.role==='viewer')return;let x=Object.fromEntries(new FormData(e.target)),old=x.oldId;if(db.farmers.some(f=>f.id===x.id&&f.id!==old))return alert('رقم العضوية مستخدم');if(old){let f=db.farmers.find(f=>f.id===old);Object.assign(f,x);if(old!==x.id){db.crops.forEach(c=>{if(c.farmerId===old)c.farmerId=x.id});db.finance.forEach(c=>{if(c.farmerId===old)c.farmerId=x.id})}}else db.farmers.push(x);resetForm('farmerForm');save()};"
new_submit = "$('farmerForm').onsubmit=e=>{e.preventDefault();if(currentUser.role==='viewer')return;let x=Object.fromEntries(new FormData(e.target)),old=x.oldId;delete x.oldId;if(old){let f=db.farmers.find(f=>f.id===old);if(!f)return alert('تعذر العثور على سجل المزارع');x.id=old;Object.assign(f,x)}else{x.id=uid();db.farmers.push(x)}resetForm('farmerForm');save()};"
assert old_submit in s
s = s.replace(old_submit, new_submit)
s = s.replace("1400/Math.max(im.width,im.height)", "1200/Math.max(im.width,im.height)")
s = s.replace("c.toDataURL('image/jpeg',.72)", "c.toDataURL('image/jpeg',.62)")
s = s.replace("x.attachment=await fileToData(fd.get('attachment'));x.amount", "try{x.attachment=await fileToData(fd.get('attachment'))}catch(err){return alert(err.message)}x.amount")
s = s.replace("village:['القرية','المحل','العزلة','village'],phone:", "village:['القرية','المحل','village'],isolation:['العزلة','isolation'],directorate:['المديرية','directorate'],governorate:['المحافظة','governorate'],phone:")
s = s.replace("!['id','name','village','phone','cardType','cardNumber','membership','status'].includes(field)", "!['id','name','village','isolation','directorate','governorate','phone','cardType','cardNumber','membership','status'].includes(field)")
s = s.replace("out.cardNumber=String(out.cardNumber??'').trim();out.membership=", "out.cardNumber=String(out.cardNumber??'').trim();out.isolation=String(out.isolation??'').trim();out.directorate=String(out.directorate||'باجل').trim();out.governorate=String(out.governorate||'الحديدة').trim();out.membership=")
# Mobile-first layout repair: keep login centered and prevent horizontal overflow on phones.
if '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' not in s:
    s = s.replace('<meta name="viewport" content="width=device-width,initial-scale=1">', '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')
responsive_css = """
<style id="bajil-mobile-layout-v8">
html,body{width:100%;max-width:100%;min-width:0;margin:0;overflow-x:hidden}
*,*::before,*::after{box-sizing:border-box}
#login{position:fixed!important;inset:0!important;width:100%!important;min-width:0!important;max-width:100%!important;min-height:100vh;min-height:100dvh;display:flex!important;flex-direction:column;align-items:center!important;justify-content:center!important;padding:16px!important;overflow-y:auto!important;overflow-x:hidden!important}
#login>.loginbox{display:block!important;float:none!important;position:relative!important;inset:auto!important;width:min(100%,440px)!important;max-width:100%!important;min-width:0!important;margin:auto!important;padding:clamp(14px,3.5vw,25px)!important;text-align:center!important}
#login .brand-logo{width:clamp(82px,20vw,150px)!important;max-height:88px!important;object-fit:contain!important}
#login .loginbox h2{font-size:clamp(15px,2.4vw,20px)!important;line-height:1.5!important;margin:8px 0!important}
#login .loginbox p{font-size:clamp(11px,1.8vw,13px)!important;overflow-wrap:anywhere}
#login .loginbox input,#login .loginbox button{width:100%!important;max-width:100%!important;min-height:44px;font-size:16px!important}
#app,.wrap,header,.panel,.formbox{min-width:0;max-width:100%}
.wrap{width:100%;padding-inline:clamp(8px,2vw,18px)}
img,video,canvas{max-width:100%;height:auto}
input,select,textarea,button{max-width:100%;min-width:0}
.tablewrap{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
@media(max-width:600px){.grid{grid-template-columns:minmax(0,1fr)!important}.kpis{grid-template-columns:repeat(2,minmax(0,1fr))!important}.tabs{gap:6px}.tabs button,.buttons button{flex:1 1 auto}.panel{padding:10px!important}header{padding:12px 10px!important}header h1{font-size:16px!important}}
@media(orientation:landscape) and (max-height:520px){#login{justify-content:flex-start!important;padding:8px!important}#login>.loginbox{margin:auto!important;padding:8px 14px!important;width:min(100%,560px)!important}#login .brand-logo{width:64px!important;max-height:46px!important;margin-bottom:2px!important}#login .loginbox h2{font-size:14px!important;margin:2px 0!important}#login .loginbox p{margin:3px 0!important}#login .loginbox .field{margin:5px 0!important}#login .loginbox input,#login .loginbox button{min-height:36px!important;padding:6px 9px!important}}
</style>
"""
if 'id="bajil-mobile-layout-v8"' not in s:
    s = s.replace("</head>", responsive_css + "\n</head>")
# Normalize escaped line-break sequences from the bundled HTML before packaging; browsers must receive real line breaks.
# Repair the CSV line-splitting regex if an earlier text transformation split its escape sequence.
bad_csv_regex = "split(/" + chr(92) + "r?" + chr(10) + "/)"
good_csv_regex = "split(/" + chr(92) + "r?" + chr(92) + "n/)"
s = s.replace(bad_csv_regex, good_csv_regex)
if "split(/" + chr(92) + "r?" + chr(10) + "/)" in s:
    raise SystemExit("CSV parser regex still contains a literal newline")

html.write_text(s, encoding="utf-8")

main = root / "app/src/main/java/ye/org/bajil/association/MainActivity.java"
main.write_text(r'''package ye.org.bajil.association;
import android.app.Activity;
import android.content.Intent;
import android.content.ContentValues;
import android.content.ClipData;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Build;
import android.provider.MediaStore;
import android.webkit.*;
import android.util.Base64;
import androidx.core.content.FileProvider;
import androidx.webkit.WebViewAssetLoader;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
public class MainActivity extends Activity {
  private WebView webView; private ValueCallback<Uri[]> fileCallback; private Uri cameraUri;
  private static final int PICK_FILE=8124; private WebViewAssetLoader assetLoader;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    assetLoader=new WebViewAssetLoader.Builder().addPathHandler("/assets/",new WebViewAssetLoader.AssetsPathHandler(this)).build();
    webView=new WebView(this); setContentView(webView); WebSettings settings=webView.getSettings();
    settings.setJavaScriptEnabled(true); settings.setDomStorageEnabled(true); settings.setDatabaseEnabled(true);
    settings.setAllowFileAccess(false); settings.setAllowContentAccess(true); settings.setLoadsImagesAutomatically(true);
    settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
    webView.addJavascriptInterface(new PhoneFiles(),"AndroidBridge");
    webView.setWebChromeClient(new WebChromeClient() {
      @Override public boolean onShowFileChooser(WebView view,ValueCallback<Uri[]> callback,FileChooserParams params) {
        if(fileCallback!=null) fileCallback.onReceiveValue(null); fileCallback=callback;
        boolean image=false; String[] types=params.getAcceptTypes();
        if(types!=null) for(String t:types) if(t!=null && (t.contains("image") || t.equals("*/*"))) image=true;
        if(image) openImageChooser(); else openDocumentPicker(); return true;
      }
    });
    webView.setWebViewClient(new WebViewClient() {
      @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest request) {
        return assetLoader.shouldInterceptRequest(request.getUrl());
      }
    });
    webView.loadUrl("https://appassets.androidplatform.net/assets/index.html");
  }
  private class PhoneFiles {
    @JavascriptInterface public void saveBase64(String name,String mime,String encoded) {
      try {
        byte[] bytes=Base64.decode(encoded,Base64.DEFAULT);
        if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q) {
          ContentValues v=new ContentValues(); v.put(MediaStore.Downloads.DISPLAY_NAME,name);
          v.put(MediaStore.Downloads.MIME_TYPE,mime); v.put(MediaStore.Downloads.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/Bajil Association");
          v.put(MediaStore.Downloads.IS_PENDING,1); Uri uri=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,v);
          if(uri==null) throw new IOException("تعذر إنشاء الملف");
          try(OutputStream out=getContentResolver().openOutputStream(uri)){out.write(bytes);}
          v.clear(); v.put(MediaStore.Downloads.IS_PENDING,0); getContentResolver().update(uri,v,null,null);
        } else {
          File dir=getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS); if(dir==null) throw new IOException("مساحة التخزين غير متاحة");
          try(FileOutputStream out=new FileOutputStream(new File(dir,name))){out.write(bytes);}
        }
        webView.post(()->webView.evaluateJavascript("alert('تم حفظ الملف في التنزيلات')",null));
      } catch(Exception ex) {
        String msg=ex.getMessage()==null?"تعذر حفظ الملف":ex.getMessage();
        webView.post(()->webView.evaluateJavascript("alert("+org.json.JSONObject.quote(msg)+")",null));
      }
    }
  }
  private void openDocumentPicker() {
    Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT); i.addCategory(Intent.CATEGORY_OPENABLE); i.setType("*/*");
    startActivityForResult(i,PICK_FILE);
  }
  private void openImageChooser() {
    Intent gallery=new Intent(Intent.ACTION_GET_CONTENT); gallery.addCategory(Intent.CATEGORY_OPENABLE); gallery.setType("image/*");
    Intent chooser=Intent.createChooser(gallery,"اختر صورة الفاتورة أو التقط صورة بالكاميرا");
    try {
      File dir=new File(getCacheDir(),"invoice_images"); if(!dir.exists()) dir.mkdirs();
      File photo=new File(dir,"invoice_"+new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(new Date())+".jpg");
      cameraUri=FileProvider.getUriForFile(this,getPackageName()+".fileprovider",photo);
      Intent camera=new Intent(MediaStore.ACTION_IMAGE_CAPTURE); camera.putExtra(MediaStore.EXTRA_OUTPUT,cameraUri);
      camera.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
      camera.setClipData(ClipData.newUri(getContentResolver(),"Invoice",cameraUri));
      chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS,new Intent[]{camera});
    } catch(Exception ex) { cameraUri=null; }
    startActivityForResult(chooser,PICK_FILE);
  }
  @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
    super.onActivityResult(requestCode,resultCode,data); if(requestCode!=PICK_FILE) return; Uri selected=null;
    if(resultCode==RESULT_OK) {
      if(cameraUri!=null) { File dir=new File(getCacheDir(),"invoice_images"); File[] files=dir.listFiles();
        if(files!=null) for(File f:files) if(f.length()>0 && cameraUri.toString().contains(f.getName())) selected=cameraUri;
      }
      if(selected==null && data!=null) selected=data.getData();
    }
    if(fileCallback!=null) { fileCallback.onReceiveValue(selected==null?null:new Uri[]{selected}); fileCallback=null; }
    cameraUri=null;
  }
  @Override public void onBackPressed() { if(webView!=null && webView.canGoBack()) webView.goBack(); else super.onBackPressed(); }
}
''', encoding="utf-8")

manifest = root / "app/src/main/AndroidManifest.xml"
ms = manifest.read_text(encoding="utf-8")
if "androidx.core.content.FileProvider" not in ms:
  provider = '''        <provider android:name="androidx.core.content.FileProvider"
            android:authorities="APPID_TOKEN.fileprovider" android:exported="false"
            android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths" />
        </provider>
'''
  provider = provider.replace("APPID_TOKEN", chr(36) + "{applicationId}")
  ms = ms.replace("    </application>", provider + "    </application>")
manifest.write_text(ms, encoding="utf-8")
res = root / "app/src/main/res/xml"; res.mkdir(parents=True, exist_ok=True)
(res / "file_paths.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android"><cache-path name="invoice_images" path="invoice_images/" /></paths>
''', encoding="utf-8")
gradle = root / "app/build.gradle"; gs = gradle.read_text(encoding="utf-8")
if "androidx.core:core" not in gs:
  gs = gs.replace("dependencies {", "dependencies {" + chr(10) + "    implementation 'androidx.core:core:1.13.1'")
gradle.write_text(gs, encoding="utf-8")
print("Applied v8 farmer fields, IndexedDB persistence, invoice camera/gallery and Android file storage.")
