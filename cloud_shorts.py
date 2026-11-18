import os, re, json, time, html, base64, hashlib, shutil, subprocess, smtplib, ssl, datetime, requests
from edu_pdf import build_pdf
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ENV = os.environ
BFILE = "bot_config.json"
bcfg = json.load(open(BFILE))
now = datetime.datetime.utcnow()
today = now.strftime("%Y-%m-%d")
if bcfg.get("today_date") != today:
    bcfg["today_date"], bcfg["today_count"] = today, 0

if ENV.get("TRIGGER_EVENT") == "schedule":
    if bcfg["today_count"] >= int(bcfg.get("daily_limit", 2)):
        print("Daily limit reached, skipping."); exit(0)
    if bcfg.get("last_run_at"):
        hrs = (now - datetime.datetime.fromisoformat(bcfg["last_run_at"])).total_seconds() / 3600
        if hrs < float(bcfg.get("interval_hours", 6)):
            print("Interval not reached, skipping."); exit(0)

LESSONS = [
    ("English", "Noun Part 1: What is Noun? (Definition & Examples)"),
    ("Hindi", "Hindi Vyakaran Part 1: Sangya (संज्ञा) - परिभाषा और भेद"),
    ("Sanskrit", "Sanskrit Vyakaran Part 1: Karaka (कारक) - सरल परिचय"),
    ("English", "Noun Part 2: Proper vs Common Noun (Rules & Examples)"),
    ("Hindi", "Hindi Vyakaran Part 2: Sarvanam (सर्वनाम) - परिभाषा और प्रकार"),
    ("Sanskrit", "Sanskrit Vyakaran Part 2: Vibhakti (विभक्ति) - प्रथम से सप्तमी")
]
idx = int(bcfg.get("lesson_idx", 0)) % len(LESSONS)
subj = ENV.get("CUSTOM_SUBJ") or LESSONS[idx][0]
topic = ENV.get("CUSTOM_TOPIC") or LESSONS[idx][1]
voice = "hi-IN-MadhurNeural" if subj == "English" else "hi-IN-SwaraNeural"
print(f"📚 [{subj}] {topic}")

prompt = f"""Teach '{topic}' ({subj} Grammar) as a 60s Indian Educational Short. Return ONLY valid JSON:
{{"title":"Catchy title (max 55 chars)","hashtags":"#{subj}Grammar #AasmaShorts #Study","scenes":[{{"hindi_speech":"Natural Hindi/Hinglish line (12-18 words)","caption":"3 words Hinglish","image_prompt":"Colorful 3D educational illustration, no text"}}],"pdf_notes":{{"summary":"4-5 line clear explanation in Hindi (Devanagari) + English","rules":["Rule 1","Rule 2","Rule 3","Rule 4"],"trick":"1-line exam shortcut","examples":["Ex 1","Ex 2","Ex 3","Ex 4"],"quiz":[{{"q":"Q1?","options":["A) ..","B) ..","C) ..","D) .."],"ans":"A"}},{{"q":"Q2?","options":["A) ..","B) ..","C) ..","D) .."],"ans":"B"}},{{"q":"Q3?","options":["A) ..","B) ..","C) ..","D) .."],"ans":"C"}},{{"q":"Q4?","options":["A) ..","B) ..","C) ..","D) .."],"ans":"D"}},{{"q":"Q5?","options":["A) ..","B) ..","C) ..","D) .."],"ans":"A"}}],"homework":["HW 1","HW 2","HW 3"]}}}}
Create exactly 8 scenes."""

data = None
for gk in [k.strip() for k in ENV["GEMINI_KEYS"].split(",") if k.strip()]:
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={gk}", json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json"}}, timeout=60)
        if r.status_code == 200:
            data = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"]); break
    except Exception: continue
if not data: raise RuntimeError("All Gemini Keys failed")

open("speak.js","w").write('const{MsEdgeTTS,OUTPUT_FORMAT}=require("msedge-tts"),fs=require("fs");(async()=>{const d=process.argv[2],t=process.argv[3],v=process.argv[4];fs.mkdirSync(d,{recursive:true});const s=new MsEdgeTTS();await s.setMetadata(v,OUTPUT_FORMAT.AUDIO_24KHZ_48KBITRATE_MONO_MP3);await s.toFile(d,t,{rate:"+4%"});})();')

WORK = "work"; shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK, exist_ok=True)
clips = []
ft = lambda x: f"{int(x//3600)}:{int((x%3600)//60):02d}:{x%60:05.2f}"
for i, sc in enumerate(data["scenes"]):
    sd = f"{WORK}/s{i}"; os.makedirs(sd, exist_ok=True)
    subprocess.run(["node", "speak.js", sd, sc["hindi_speech"], voice], check=True)
    aud = f"{sd}/audio.mp3"
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",aud]).decode().strip())
    img = f"{sd}/img.png"
    cf = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{ENV['CF_ACCOUNT_ID']}/ai/run/@cf/black-forest-labs/flux-1-schnell", headers={"Authorization":f"Bearer {ENV['CF_API_TOKEN']}"}, json={"prompt":sc["image_prompt"]}, timeout=60)
    if cf.status_code==200 and cf.json().get("result",{}).get("image"):
        open(img,"wb").write(base64.b64decode(cf.json()["result"]["image"]))
    else:
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i","color=c=#1e293b:s=720x1280","-frames:v","1",img], check=True)
    wds = re.sub(r"[{}]", "", sc["hindi_speech"]).split()
    cks = [" ".join(wds[k:k+3]) for k in range(0, len(wds), 3)] or [sc["caption"]]
    cd = dur / len(cks)
    dlgs = "\n".join(f"Dialogue: 0,{ft(k*cd)},{ft((k+1)*cd)},Default,{{\\fscx85\\fscy85\\t(0,80,\\fscx100\\fscy100)}}{c}" for k, c in enumerate(cks))
    ass = f"{sd}/sub.ass"
    open(ass,"w").write(f"[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV\nStyle: Default,Sans,44,&H0000FFFF,&H80000000,-1,4,10,0,2,30,130,260\n[Events]\nFormat: Layer, Start, End, Style, Text\n{dlgs}\n")
    clip = f"{WORK}/c{i}.mp4"; fr = max(20, int(dur*20))
    zp = f"zoompan=z='min(zoom+0.0015,1.2)':d={fr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280:fps=20" if i%2==0 else f"zoompan=z='if(lte(zoom,1.0),1.2,max(1.001,zoom-0.0015))':d={fr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280:fps=20"
    subprocess.run(["ffmpeg","-y","-loop","1","-i",img,"-i",aud,"-vf",f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,{zp},ass={ass}","-c:v","libx264","-preset","ultrafast","-crf","26","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",clip], check=True)
    clips.append(clip)

open(f"{WORK}/l.txt","w").write("\n".join(f"file '{os.path.abspath(c)}'" for c in clips))
safe = re.sub(r'[^a-zA-Z0-9_-]','_',data["title"])[:35]
mp4 = f"{WORK}/{safe}.mp4"; pdf_p = f"{WORK}/{safe}_Aasma_Shorts.pdf"
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",f"{WORK}/l.txt","-c","copy","-movflags","+faststart",mp4], check=True)
build_pdf(pdf_p, subj, topic, data["pdf_notes"])

ts = int(time.time()); pid = f"vid_{safe}_{ts}"
sig = hashlib.sha1(f"folder=aasma_videos&public_id={pid}&timestamp={ts}{ENV['CLOUD_API_SECRET']}".encode()).hexdigest()
vid_url = requests.post(f"https://api.cloudinary.com/v1_1/{ENV['CLOUD_NAME']}/video/upload", data={"api_key":ENV["CLOUD_API_KEY"],"timestamp":ts,"folder":"aasma_videos","public_id":pid,"signature":sig}, files={"file":open(mp4,"rb")}, timeout=300).json()["secure_url"]
stream_url = vid_url.replace("/upload/", "/upload/q_auto:eco,f_mp4/")
thumb_url = vid_url.replace("/upload/", "/upload/so_0,w_480,q_auto/").rsplit(".", 1)[0] + ".jpg"

tg_v = requests.post(f"https://api.telegram.org/bot{ENV['TG_TOKEN']}/sendVideo", data={"chat_id":"@aasma_shorts_study","supports_streaming":True,"width":720,"height":1280,"caption":f"📚 {data['title']}\n\n{data['hashtags']}"}, files={"video":open(mp4,"rb")}, timeout=300).json()
tg_p = requests.post(f"https://api.telegram.org/bot{ENV['TG_TOKEN']}/sendDocument", data={"chat_id":"@aasma_shorts_study","caption":f"📄 {data['title']} - PDF Notes"}, files={"document":open(pdf_p,"rb")}, timeout=120).json()
pdf_tg = f"https://t.me/aasma_shorts_study/{tg_p['result']['message_id']}"

n = data["pdf_notes"]; hw = " | ".join(n["homework"])
b_html = f'<div class="edu-meta" data-subject="{subj}" data-video="{html.escape(stream_url)}" data-tg-post="aasma_shorts_study/{tg_v["result"]["message_id"]}" data-pdf="{html.escape(pdf_tg)}" data-thumb="{html.escape(thumb_url)}" data-summary="{html.escape(n["summary"])}" data-homework="{html.escape(hw)}"></div><p>{html.escape(n["summary"])}</p>'
msg = MIMEMultipart("alternative"); msg["Subject"] = data["title"]; msg["From"] = ENV["GMAIL"]; msg["To"] = ENV["BLOGGER_EMAIL"]
msg.attach(MIMEText(b_html, "html"))
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
    s.login(ENV["GMAIL"], ENV["APP_PASSWORD"]); s.sendmail(ENV["GMAIL"], ENV["BLOGGER_EMAIL"], msg.as_string())

try:
    time.sleep(12)
    fd = requests.get(f"{ENV['BLOG_URL'].rstrip('/')}/feeds/posts/default?alt=json&max-results=1", timeout=15).json()
    purl = [l["href"] for l in fd["feed"]["entry"][0]["link"] if l["rel"] == "alternate"][0]
    requests.post(f"https://api.telegram.org/bot{ENV['TG_TOKEN']}/editMessageCaption", data={"chat_id":"@aasma_shorts_study","message_id":tg_v["result"]["message_id"],"caption":f"📚 {data['title']}\n\n🌐 Watch & Notes: {purl}\n👇 Free PDF Niche Hai!\n\n{data['hashtags']}"}, timeout=30)
except Exception: pass

if not ENV.get("CUSTOM_TOPIC"): bcfg["lesson_idx"] = idx + 1
bcfg["today_count"] += 1; bcfg["last_run_at"] = now.isoformat(); bcfg["last_status"] = f"OK: {data['title']}"
json.dump(bcfg, open(BFILE, "w"), indent=2)
subprocess.run(["git","config","user.name","AasmaBot"]); subprocess.run(["git","config","user.email","bot@aasma.local"])
subprocess.run(["git","add",BFILE]); subprocess.run(["git","commit","-m","Update bot_config"]); subprocess.run(["git","push"])
requests.post(f"https://api.telegram.org/bot{ENV['TG_TOKEN']}/sendMessage", json={"chat_id":"8990607208","text":f"✅ Done! [{subj}] {data['title']} ban gaya aur Telegram + Blogger par post ho gaya!"}, timeout=20)
print("🎉 CLOUD RUN COMPLETE!") # ADMIN_ALERT_ADDED
