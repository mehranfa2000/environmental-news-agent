# ============================================================
#  health.py  —  سلامت‌سنجی منابع RSS
#  منابع خراب خودکار غیرفعال، منابع بهبودیافته خودکار فعال می‌شوند
# ============================================================

import json
import logging
import os
from datetime import datetime, timezone
import pytz
import jdatetime
from config import (
    HEALTH_FILE, HEALTH_FAILURE_THRESHOLD,
    HEALTH_RECOVERY_CHECKS, HEALTH_SLOW_THRESHOLD_MS,
    DATA_DIR, TIMEZONE
)

logger = logging.getLogger(__name__)

TEHRAN_TZ = pytz.timezone(TIMEZONE)


def _now_str() -> str:
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TEHRAN_TZ)
    jd  = jdatetime.datetime.fromgregorian(datetime=now)
    return jd.strftime("%Y-%m-%d %H:%M")


class HealthMonitor:
    """ردیابی وضعیت سلامت هر منبع RSS."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(HEALTH_FILE):
            try:
                with open(HEALTH_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(HEALTH_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("❌ خطا در ذخیره health.json: %s", e)

    def _get(self, name: str) -> dict:
        """رکورد سلامت یک منبع را برمی‌گردد (ایجاد می‌کند اگر نباشد)."""
        if name not in self._data:
            self._data[name] = {
                "status":               "unknown",
                "consecutive_failures": 0,
                "consecutive_successes": 0,
                "total_checks":         0,
                "total_successes":      0,
                "total_items":          0,
                "avg_response_ms":      0,
                "last_success":         None,
                "last_failure":         None,
                "auto_disabled":        False,
                "disabled_since":       None,
            }
        return self._data[name]

    def update(self, fetch_result: dict):
        """
        نتیجه دریافت یک منبع را ثبت می‌کند.
        fetch_result: خروجی fetcher._fetch_one()
        """
        name       = fetch_result["name"]
        success    = fetch_result["success"]
        resp_ms    = fetch_result.get("response_ms", 0)
        item_count = len(fetch_result.get("items", []))

        rec = self._get(name)
        rec["total_checks"] += 1

        # میانگین متحرک زمان پاسخ
        if resp_ms > 0:
            prev_avg = rec["avg_response_ms"]
            rec["avg_response_ms"] = int(
                (prev_avg * (rec["total_checks"] - 1) + resp_ms) / rec["total_checks"]
            )

        if success:
            rec["consecutive_failures"]  = 0
            rec["consecutive_successes"] += 1
            rec["total_successes"]       += 1
            rec["total_items"]           += item_count
            rec["last_success"]          = _now_str()

            # بازفعال‌سازی خودکار
            if rec["auto_disabled"] and rec["consecutive_successes"] >= HEALTH_RECOVERY_CHECKS:
                rec["auto_disabled"]  = False
                rec["disabled_since"] = None
                rec["status"]         = "recovered"
                logger.info("✅ منبع بازفعال شد: %s", name)
            elif not rec["auto_disabled"]:
                if resp_ms > HEALTH_SLOW_THRESHOLD_MS:
                    rec["status"] = "slow"
                else:
                    rec["status"] = "healthy"
        else:
            rec["consecutive_failures"]  += 1
            rec["consecutive_successes"]  = 0
            rec["last_failure"]           = _now_str()

            # غیرفعال‌سازی خودکار
            if rec["consecutive_failures"] >= HEALTH_FAILURE_THRESHOLD and not rec["auto_disabled"]:
                rec["auto_disabled"]  = True
                rec["disabled_since"] = _now_str()
                rec["status"]         = "disabled"
                logger.warning("🚫 منبع غیرفعال شد: %s (%d خطای متوالی)", name, rec["consecutive_failures"])
            elif not rec["auto_disabled"]:
                rec["status"] = "failing"

        self._data[name] = rec

    def is_disabled(self, name: str) -> bool:
        """آیا منبع غیرفعال است؟"""
        return self._data.get(name, {}).get("auto_disabled", False)

    def get_active_sources(self, all_sources: list[tuple]) -> list[tuple]:
        """
        منابع فعال را از لیست کامل فیلتر می‌کند.
        """
        active   = []
        disabled = []
        for src in all_sources:
            name = src[0]
            if self.is_disabled(name):
                disabled.append(name)
            else:
                active.append(src)

        if disabled:
            logger.info("🚫 %d منبع غیرفعال (نادیده گرفته شد): %s",
                        len(disabled), ", ".join(disabled[:5]))
        return active

    def update_batch(self, fetch_results: list[dict]):
        """نتایج دریافت همه منابع را ثبت می‌کند."""
        for result in fetch_results:
            self.update(result)
        self._save()

    def summary(self) -> dict:
        """خلاصه آماری سلامت منابع."""
        total    = len(self._data)
        healthy  = sum(1 for r in self._data.values() if r["status"] in ("healthy", "recovered"))
        slow     = sum(1 for r in self._data.values() if r["status"] == "slow")
        failing  = sum(1 for r in self._data.values() if r["status"] == "failing")
        disabled = sum(1 for r in self._data.values() if r["auto_disabled"])
        return {
            "total": total,
            "healthy": healthy,
            "slow": slow,
            "failing": failing,
            "disabled": disabled,
        }

    def get_all(self) -> dict:
        return self._data
