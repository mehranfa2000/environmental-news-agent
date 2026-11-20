# ================================================================
#  📨 ماژول ارسال پیام به تلگرام و بله
# ================================================================

import os
import time
import logging
import requests

log = logging.getLogger(__name__)

RETRY_ATTEMPTS = 4
RETRY_DELAYS   = [3, 7, 15, 30]   # تاخیر تصاعدی (ثانیه)
TIMEOUT        = 20

def _post(url: str, payload: dict, label: str) -> bool:
    """ارسال POST با مکانیزم Retry تصاعدی"""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            resp = requests.post(url, json=payload, timeout=TIMEOUT)
            if resp.status_code == 200:
                return True
            # اگر Too Many Requests → صبر بیشتر
            if resp.status_code == 429:
                retry_after = int(resp.headers.get('Retry-After', 60))
                log.warning(f"[{label}] Too Many Requests — صبر {retry_after} ثانیه")
                time.sleep(retry_after)
                continue
            log.warning(f"[{label}] تلاش {attempt+1}: کد {resp.status_code} — {resp.text[:120]}")
        except requests.exceptions.Timeout:
            log.warning(f"[{label}] تلاش {attempt+1}: Timeout")
        except requests.exceptions.ConnectionError as e:
            log.warning(f"[{label}] تلاش {attempt+1}: خطای اتصال — {e}")
        except Exception as e:
            log.error(f"[{label}] تلاش {attempt+1}: خطای ناشناخته — {e}")

        if attempt < RETRY_ATTEMPTS - 1:
            time.sleep(RETRY_DELAYS[attempt])

    log.error(f"[{label}] تمام {RETRY_ATTEMPTS} تلاش ناموفق بود.")
    return False

def send_telegram(tg_text: str) -> bool:
    token   = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHANNEL_ID', '').strip()
    if not token or not chat_id:
        log.error("[Telegram] توکن یا Chat ID تنظیم نشده.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id":                  chat_id,
        "text":                     tg_text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": False,
    }
    return _post(url, payload, "Telegram")

def send_bale(bale_text: str) -> bool:
    token   = os.getenv('BALE_BOT_TOKEN', '').strip()
    chat_id = os.getenv('BALE_CHANNEL_ID', '').strip()
    if not token or not chat_id:
        log.error("[Bale] توکن یا Chat ID تنظیم نشده.")
        return False
    url = f"https://tapi.bale.ai/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text":    bale_text,
    }
    return _post(url, payload, "Bale")
