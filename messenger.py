import requests
import time
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID,
    BALE_BOT_TOKEN, BALE_CHANNEL_ID
)
from formatter import format_telegram, format_bale

# آدرس‌های API
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
BALE_API = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}"

# تعداد تلاش مجدد در صورت خطا
MAX_RETRIES = 3
RETRY_DELAY = 5  # ثانیه


def send_telegram(item):
    """ارسال خبر به کانال تلگرام"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("  ⚠️ تلگرام: توکن یا آیدی کانال تنظیم نشده")
        return False

    message = format_telegram(item)

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=30
            )

            data = response.json()

            if data.get("ok"):
                print(f"  ✅ تلگرام: ارسال موفق")
                return True
            else:
                error = data.get("description", "خطای نامشخص")
                print(f"  ❌ تلگرام: {error}")

                # اگر خطای محدودیت نرخ بود، صبر می‌کنیم
                if "retry_after" in str(error).lower() or "too many" in str(error).lower():
                    wait = data.get("parameters", {}).get("retry_after", 30)
                    print(f"  ⏳ صبر {wait} ثانیه...")
                    time.sleep(wait)
                    continue

                return False

        except requests.exceptions.Timeout:
            print(f"  ⏱️ تلگرام: Timeout (تلاش {attempt + 1})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        except Exception as e:
            print(f"  ❌ تلگرام: {type(e).__name__}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return False


def send_bale(item):
    """ارسال خبر به کانال بله"""
    if not BALE_BOT_TOKEN or not BALE_CHANNEL_ID:
        print("  ⚠️ بله: توکن یا آیدی کانال تنظیم نشده")
        return False

    message = format_bale(item)

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{BALE_API}/sendMessage",
                json={
                    "chat_id": BALE_CHANNEL_ID,
                    "text": message,
                },
                timeout=30
            )

            data = response.json()

            if data.get("ok"):
                print(f"  ✅ بله: ارسال موفق")
                return True
            else:
                error = data.get("description", "خطای نامشخص")
                print(f"  ❌ بله: {error}")
                return False

        except requests.exceptions.Timeout:
            print(f"  ⏱️ بله: Timeout (تلاش {attempt + 1})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        except Exception as e:
            print(f"  ❌ بله: {type(e).__name__}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return False


def send_item(item):
    """
    ارسال یک خبر به هر دو کانال تلگرام و بله
    خروجی: دیکشنری نتیجه ارسال
    """
    title = item.get("title", "")[:50]
    print(f"\n  📤 ارسال: {title}...")

    tg_ok = send_telegram(item)
    time.sleep(2)  # فاصله بین ارسال به دو پلتفرم
    bale_ok = send_bale(item)

    return {
        "telegram": tg_ok,
        "bale": bale_ok,
        "sent": tg_ok or bale_ok
    }


def send_all(items):
    """
    ارسال همه اخبار به هر دو کانال
    خروجی: لیست اخبار ارسال شده + آمار
    """
    if not items:
        print("\n[Messenger] هیچ خبری برای ارسال وجود ندارد.")
        return [], {"total_sent": 0, "tg_sent": 0, "bale_sent": 0}

    print(f"\n[Messenger] ارسال {len(items)} خبر...")

    sent_items = []
    tg_count = 0
    bale_count = 0

    for i, item in enumerate(items, 1):
        print(f"\n[{i}/{len(items)}]", end="")

        result = send_item(item)

        if result["sent"]:
            sent_items.append(item)

        if result["telegram"]:
            tg_count += 1

        if result["bale"]:
            bale_count += 1

        # فاصله بین ارسال اخبار (جلوگیری از محدودیت نرخ)
        if i < len(items):
            time.sleep(3)

    print(f"\n[Messenger] نتیجه:")
    print(f"  📤 کل ارسال شده: {len(sent_items)}")
    print(f"  ✈️ تلگرام: {tg_count}")
    print(f"  💬 بله: {bale_count}")

    stats = {
        "total_sent": len(sent_items),
        "tg_sent": tg_count,
        "bale_sent": bale_count,
    }

    return sent_items, stats
