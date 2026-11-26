from pathlib import Path
p=Path("bajil_android_project/app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
a=s.find("async function load(){")
b=s.find("\\nfunction save(){",a)
if a<0 or b<0: raise SystemExit("Database loader not found")
new="""async function load(){
 let d=null;
 try{d=await readStoredState()}catch(e){console.warn('Database read failed',e)}
 if(d&&typeof d==='object'&&!Array.isArray(d))db={...db,...d};
 for(const k of ['farmers','crops','inventory','finance','movements','users','journal','cashOps'])if(!Array.isArray(db[k]))db[k]=[];
 db.counters={receipt:0,payment:0,...(db.counters||{})};
 db.farmers=db.farmers.map(f=>({...f,cardType:f.cardType||'',cardNumber:f.cardNumber||'',village:f.village||'',isolation:f.isolation||'',directorate:f.directorate||'باجل',governorate:f.governorate||'الحديدة',membership:f.membership||'غير منتسب للجمعية',phone:f.phone||'',notes:f.notes||''}));
 db.users=db.users.map(u=>({...u,username:String(u.username??'').trim(),password:String(u.password??''),role:u.role||'staff',active:u.active===false||u.active==='false'?false:true}));
 if(!db.users.length)db.users=[{username:'الخلفية',password:'1234',role:'admin',active:true}];
}"""
s=s[:a]+new+s[b:]
p.write_text(s,encoding="utf-8")
