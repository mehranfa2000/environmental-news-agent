# ================================================================
#  health.py — سلامت‌سنجی منابع
# ================================================================
import json, logging, os
from datetime import datetime
import pytz, jdatetime
from config import (HEALTH_FILE, FAIL_THRESHOLD,
                    RECOVERY_CHECKS, SLOW_THRESHOLD_MS,
                    DATA_DIR, TIMEZONE)

logger = logging.getLogger(__name__)
TZ = pytz.timezone(TIMEZONE)

WEEKDAYS = {0:"دوشنبه",1:"سه‌شنبه",2:"چهارشنبه",
            3:"پنج‌شنبه",4:"جمعه",5:"شنبه",6:"یکشنبه"}
MONTHS   = ["","فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
            "مهر","آبان","آذر","دی","بهمن","اسفند"]


def _now():
    n  = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
    jd = jdatetime.datetime.fromgregorian(datetime=n)
    return f"{WEEKDAYS[jd.weekday()]} {jd.day} {MONTHS[jd.month]} {jd.strftime('%H:%M')}"


class HealthMonitor:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._d = self._load()

    def _load(self):
        if os.path.exists(HEALTH_FILE):
            try:
                with open(HEALTH_FILE,"r",encoding="utf-8") as f:
                    return json.load(f)
            except Exception: pass
        return {}

    def _save(self):
        try:
            with open(HEALTH_FILE,"w",encoding="utf-8") as f:
                json.dump(self._d,f,ensure_ascii=False,indent=2)
        except Exception as e: logger.error("health save: %s",e)

    def _rec(self, name):
        if name not in self._d:
            self._d[name] = {
                "status":"unknown","consec_fail":0,"consec_ok":0,
                "total_checks":0,"total_ok":0,"total_items":0,
                "avg_ms":0,"last_ok":None,"last_fail":None,
                "disabled":False,"disabled_since":None}
        return self._d[name]

    def update(self, r):
        name = r["name"]; ok = r["success"]; ms = r.get("ms",0)
        rec  = self._rec(name)
        rec["total_checks"] += 1
        if ms>0:
            prev = rec["avg_ms"]
            rec["avg_ms"] = int((prev*(rec["total_checks"]-1)+ms)/rec["total_checks"])

        if ok:
            rec["consec_fail"] = 0; rec["consec_ok"] += 1
            rec["total_ok"] += 1; rec["total_items"] += len(r.get("items",[]))
            rec["last_ok"] = _now()
            if rec["disabled"] and rec["consec_ok"] >= RECOVERY_CHECKS:
                rec["disabled"]=False; rec["disabled_since"]=None
                rec["status"]="recovered"
                logger.info("✅ بازفعال: %s",name)
            elif not rec["disabled"]:
                rec["status"] = "slow" if ms>SLOW_THRESHOLD_MS else "healthy"
        else:
            rec["consec_ok"]=0; rec["consec_fail"]+=1; rec["last_fail"]=_now()
            if rec["consec_fail"]>=FAIL_THRESHOLD and not rec["disabled"]:
                rec["disabled"]=True; rec["disabled_since"]=_now()
                rec["status"]="disabled"
                logger.warning("🚫 غیرفعال: %s",name)
            elif not rec["disabled"]:
                rec["status"]="failing"

        self._d[name] = rec

    def update_batch(self, results):
        for r in results: self.update(r)
        self._save()

    def is_disabled(self, name):
        return self._d.get(name,{}).get("disabled",False)

    def get_active(self, sources):
        return [s for s in sources if not self.is_disabled(s[0])]

    def summary(self):
        total    = len(self._d)
        healthy  = sum(1 for r in self._d.values() if r["status"] in ("healthy","recovered"))
        slow     = sum(1 for r in self._d.values() if r["status"]=="slow")
        failing  = sum(1 for r in self._d.values() if r["status"]=="failing")
        disabled = sum(1 for r in self._d.values() if r["disabled"])
        return {"total":total,"healthy":healthy,"slow":slow,
                "failing":failing,"disabled":disabled}
