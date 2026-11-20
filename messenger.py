# ================================================================
#  messenger.py — ارسال به تلگرام + بله + صف retry
# ================================================================
import json, logging, os, time
from datetime import datetime, timezone
import requests
from config import (RETRY_ATTEMPTS, RETRY_BASE_DELAY,
                    MAX_QUEUE_HOURS, MAX_QUEUE_SIZE,
                    QUEUE_FILE, DATA_DIR)

logger = logging.getLogger(__name__)

TG_API   = "https://api.telegram.org/bot{token}/{method}"
BALE_API = "https://tapi.bale.ai/bot{token}/{method}"


def _call(url, data, files=None):
    for attempt in range(1, RETRY_ATTEMPTS+1):
        try:
            r = (requests.post(url,data=data,files=files,timeout=30)
                 if files else
                 requests.post(url,json=data,timeout=15))
            if r.status_code==200 and r.json().get("ok"):
                return True, ""
            if r.status_code==429:
                wait = r.json().get("parameters",{}).get("retry_after",60)
                logger.warning("⏳ rate limit %ds",wait); time.sleep(wait); continue
            err = r.text[:200]
            logger.warning("⚠️ API attempt %d: %s",attempt,err)
        except requests.exceptions.Timeout:
            logger.warning("⏱️ timeout attempt %d",attempt)
        except Exception as e:
            logger.warning("❌ attempt %d: %s",attempt,e)
        if attempt < RETRY_ATTEMPTS:
            time.sleep(RETRY_BASE_DELAY * (2**(attempt-1)))
    return False, "max retries"


def send_telegram(token, channel, msg):
    text = msg["text"]; img = msg.get("image_url"); pm = msg.get("parse_mode","HTML")
    if img:
        url  = TG_API.format(token=token, method="sendPhoto")
        ok,_ = _call(url,{"chat_id":channel,"photo":img,
                           "caption":text[:1024],"parse_mode":pm})
        if ok: logger.info("📤 تلگرام ✅ (تصویر)"); return True
    url  = TG_API.format(token=token, method="sendMessage")
    ok,err = _call(url,{"chat_id":channel,"text":text[:4096],
                        "parse_mode":pm,"disable_web_page_preview":False})
    if ok: logger.info("📤 تلگرام ✅")
    else:  logger.error("📤 تلگرام ❌: %s",err)
    return ok


def send_bale(token, channel, text):
    url = BALE_API.format(token=token, method="sendMessage")
    ok,err = _call(url,{"chat_id":channel,"text":text[:4096]})
    if ok: logger.info("📤 بله ✅")
    else:  logger.error("📤 بله ❌: %s",err)
    return ok


class MsgQueue:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._q = self._load()

    def _load(self):
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE,"r",encoding="utf-8") as f: return json.load(f)
            except Exception: pass
        return []

    def _save(self):
        try:
            with open(QUEUE_FILE,"w",encoding="utf-8") as f:
                json.dump(self._q,f,ensure_ascii=False,indent=2)
        except Exception as e: logger.error("queue save: %s",e)

    def _clean(self):
        now = datetime.now(timezone.utc).timestamp()
        cut = MAX_QUEUE_HOURS*3600
        self._q = [q for q in self._q if now-q.get("at",0)<cut]
        if len(self._q)>MAX_QUEUE_SIZE: self._q=self._q[-MAX_QUEUE_SIZE:]

    def add(self, platform, payload):
        self._clean()
        self._q.append({"platform":platform,"payload":payload,
                         "at":datetime.now(timezone.utc).timestamp(),"tries":0})
        self._save()

    def retry_all(self, tgt, tgc, bat, bac):
        self._clean()
        if not self._q: return 0
        ok_count, remain = 0, []
        for e in self._q:
            pl = e["payload"]; p = e["platform"]; ok=False
            if p=="telegram": ok=send_telegram(tgt,tgc,pl)
            elif p=="bale":   ok=send_bale(bat,bac,pl)
            if ok: ok_count+=1
            else:
                e["tries"]=e.get("tries",0)+1
                if e["tries"]<5: remain.append(e)
            time.sleep(0.5)
        self._q=remain; self._save()
        return ok_count
