# ============================================================
#  messenger.py  —  ارسال به تلگرام و بله + صف پیام‌های ناموفق
# ============================================================

import json
import logging
import os
import time
from datetime import datetime, timezone
import requests
import pytz
from config import (
    SEND_RETRY_ATTEMPTS, SEND_RETRY_BASE_DELAY,
    MAX_QUEUE_AGE_HOURS, MAX_QUEUE_SIZE,
    QUEUE_FILE, DATA_DIR, TIMEZONE
)

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
BALE_API     = "https://tapi.bale.ai/bot{token}/{method}"


# ══════════════════════════════════════════════════════════════
#  توابع پایه ارسال
# ══════════════════════════════════════════════════════════════

def _call_api(url: str, data: dict, files=None) -> tuple[bool, str]:
    """یک درخواست API ارسال می‌کند. خروجی: (success, error_msg)"""
    for attempt in range(1, SEND_RETRY_ATTEMPTS + 1):
        try:
            if files:
                resp = requests.post(url, data=data, files=files, timeout=30)
            else:
                resp = requests.post(url, json=data, timeout=15)

            if resp.status_code == 200 and resp.json().get("ok"):
                return True, ""

            # Too Many Requests → صبر کن
            if resp.status_code == 429:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 60)
                logger.warning("⏳ rate limit — صبر %d ثانیه", retry_after)
                time.sleep(retry_after)
                continue

            error = resp.text[:200]
            logger.warning("⚠️ API error (attempt %d/%d): %s", attempt, SEND_RETRY_ATTEMPTS, error)

        except requests.exceptions.Timeout:
            logger.warning("⏱️ timeout (attempt %d/%d)", attempt, SEND_RETRY_ATTEMPTS)
        except Exception as e:
            logger.warning("❌ error (attempt %d/%d): %s", attempt, SEND_RETRY_ATTEMPTS, e)

        if attempt < SEND_RETRY_ATTEMPTS:
            delay = SEND_RETRY_BASE_DELAY * (2 ** (attempt - 1))   # exponential backoff
            time.sleep(delay)

    return False, "max retries exceeded"


def send_telegram(token: str, channel_id: str, msg: dict) -> bool:
    """
    ارسال به کانال تلگرام.
    msg: خروجی formatter.format_telegram()
    """
    text      = msg["text"]
    image_url = msg.get("image_url")
    parse     = msg.get("parse_mode", "HTML")

    if image_url:
        # ارسال با تصویر
        url  = TELEGRAM_API.format(token=token, method="sendPhoto")
        data = {
            "chat_id":    channel_id,
            "photo":      image_url,
            "caption":    text[:1024],   # caption max 1024 chars
            "parse_mode": parse,
        }
        ok, err = _call_api(url, data)
        if ok:
            logger.info("📤 تلگرام ✅ (با تصویر)")
            return True
        # اگر تصویر خطا داد، بدون تصویر امتحان کن
        logger.warning("🖼️ خطای تصویر، ارسال بدون تصویر: %s", err)

    # ارسال بدون تصویر
    url  = TELEGRAM_API.format(token=token, method="sendMessage")
    data = {
        "chat_id":                  channel_id,
        "text":                     text[:4096],
        "parse_mode":               parse,
        "disable_web_page_preview": False,
    }
    ok, err = _call_api(url, data)
    if ok:
        logger.info("📤 تلگرام ✅")
    else:
        logger.error("📤 تلگرام ❌: %s", err)
    return ok


def send_bale(token: str, channel_id: str, text: str) -> bool:
    """ارسال به کانال بله (متن ساده)."""
    url  = BALE_API.format(token=token, method="sendMessage")
    data = {
        "chat_id": channel_id,
        "text":    text[:4096],
    }
    ok, err = _call_api(url, data)
    if ok:
        logger.info("📤 بله ✅")
    else:
        logger.error("📤 بله ❌: %s", err)
    return ok


# ══════════════════════════════════════════════════════════════
#  صف پیام‌های ناموفق (Retry Queue)
# ══════════════════════════════════════════════════════════════

class MessageQueue:
    """پیام‌های ناموفق را ذخیره و دوباره ارسال می‌کند."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._queue = self._load()

    def _load(self) -> list:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("❌ خطا در ذخیره queue.json: %s", e)

    def _clean_old(self):
        """پیام‌های قدیمی را حذف می‌کند."""
        now  = datetime.now(timezone.utc).timestamp()
        cutoff = MAX_QUEUE_AGE_HOURS * 3600
        self._queue = [
            q for q in self._queue
            if (now - q.get("queued_at", 0)) < cutoff
        ]
        # حداکثر اندازه صف
        if len(self._queue) > MAX_QUEUE_SIZE:
            self._queue = self._queue[-MAX_QUEUE_SIZE:]

    def add(self, platform: str, payload: dict):
        """پیام ناموفق را به صف اضافه می‌کند."""
        self._clean_old()
        self._queue.append({
            "platform":  platform,
            "payload":   payload,
            "queued_at": datetime.now(timezone.utc).timestamp(),
            "attempts":  0,
        })
        self._save()
        logger.info("📋 پیام در صف ذخیره شد (platform=%s)", platform)

    def retry_all(self, tg_token: str, tg_channel: str,
                  bale_token: str, bale_channel: str) -> int:
        """
        همه پیام‌های صف را دوباره ارسال می‌کند.
        خروجی: تعداد پیام‌های موفق.
        """
        self._clean_old()
        if not self._queue:
            return 0

        logger.info("🔄 تلاش مجدد برای %d پیام در صف", len(self._queue))
        success_count = 0
        remaining     = []

        for entry in self._queue:
            platform = entry["platform"]
            payload  = entry["payload"]
            ok       = False

            if platform == "telegram":
                ok = send_telegram(tg_token, tg_channel, payload)
            elif platform == "bale":
                ok = send_bale(bale_token, bale_channel, payload)

            if ok:
                success_count += 1
                logger.info("✅ صف: پیام ارسال شد (platform=%s)", platform)
            else:
                entry["attempts"] = entry.get("attempts", 0) + 1
                if entry["attempts"] < 5:    # حداکثر ۵ تلاش
                    remaining.append(entry)

            time.sleep(0.5)   # تأخیر بین ارسال‌ها

        self._queue = remaining
        self._save()
        return success_count
