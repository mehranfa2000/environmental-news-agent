# ============================================================
#  formatter.py  —  قالب‌بندی پیام‌های تلگرام و بله
#  تلگرام: HTML + تصویر | بله: متن ساده
# ============================================================

import re
import logging
from html import unescape
from datetime import datetime
from typing import Optional
import pytz
import jdatetime
import requests
from config import TIMEZONE, FETCH_IMAGE, IMAGE_TIMEOUT_SEC

logger = logging.getLogger(__name__)

TEHRAN_TZ = pytz.timezone(TIMEZONE)

# روزهای هفته شمسی
WEEKDAYS_FA = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنج‌شنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}

# ماه‌های شمسی
MONTHS_FA = [
    "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]


def _jalali_now() -> str:
    """تاریخ و ساعت شمسی با نام روز هفته."""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    now_teh = now_utc.astimezone(TEHRAN_TZ)
    jd = jdatetime.datetime.fromgregorian(datetime=now_teh)
    weekday = WEEKDAYS_FA[jd.weekday()]
    month   = MONTHS_FA[jd.month]
    return f"{weekday} {jd.day} {month} {jd.year} — {jd.strftime('%H:%M')}"


def clean_html(text: str) -> str:
    """HTML tags را حذف، فاصله‌ها را اصلاح می‌کند."""
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def smart_summary(text: str, max_chars: int = 280) -> str:
    """
    خلاصه هوشمند: تا max_chars کاراکتر، برش در پایان جمله.
    """
    text = clean_html(text)
    if len(text) <= max_chars:
        return text

    # برش در نزدیک‌ترین نقطه قبل از max_chars
    cut = text[:max_chars]
    for sep in (".", "!", "?", "؟", "،", "\n"):
        pos = cut.rfind(sep)
        if pos > max_chars // 2:
            return cut[:pos + 1].strip()

    return cut.strip() + "…"


def _fetch_og_image(link: str) -> Optional[str]:
    """
    آدرس تصویر شاخص (og:image) را از صفحه خبر استخراج می‌کند.
    """
    if not FETCH_IMAGE:
        return None
    try:
        resp = requests.get(
            link,
            timeout=IMAGE_TIMEOUT_SEC,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return None
        # جستجوی og:image بدون BeautifulSoup (regex سریع‌تر)
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']',
            resp.text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
        # حالت معکوس attribute order
        match2 = re.search(
            r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']',
            resp.text,
            re.IGNORECASE,
        )
        if match2:
            return match2.group(1)
    except Exception:
        pass
    return None


def format_telegram(item: dict) -> dict:
    """
    پیام تلگرام را آماده می‌کند.
    خروجی: {"text": str, "image_url": Optional[str], "parse_mode": "HTML"}
    """
    urgency    = item.get("urgency", "")
    emoji      = item["category_emoji"]
    label      = item["category_label"]
    title      = item["title_clean"]
    summary    = smart_summary(item.get("summary_clean", ""))
    source     = item["source"]
    link       = item["link"]
    jalali     = _jalali_now()

    urgency_line = f"{urgency} <b>خبر فوری</b>\n" if urgency == "🔴" else (
                   f"{urgency} خبر مهم\n" if urgency == "🟠" else "")

    text = (
        f"{urgency_line}"
        f"{emoji} <b>{label}</b>\n\n"
        f"📰 <b>{title}</b>\n\n"
        f"📝 {summary}\n\n"
        f"📅 {jalali}\n"
        f"📌 منبع: {source}\n"
        f"🔗 <a href=\"{link}\">مشاهده خبر</a>"
    )

    # تصویر: ابتدا از feed، سپس og:image
    image_url = item.get("image_url")
    if not image_url:
        image_url = _fetch_og_image(link)

    return {
        "text":       text,
        "image_url":  image_url,
        "parse_mode": "HTML",
    }


def format_bale(item: dict) -> str:
    """
    پیام بله — متن ساده (بله HTML پیچیده را پشتیبانی نمی‌کند).
    """
    urgency    = item.get("urgency", "")
    emoji      = item["category_emoji"]
    label      = item["category_label"]
    title      = item["title_clean"]
    summary    = smart_summary(item.get("summary_clean", ""), max_chars=200)
    source     = item["source"]
    link       = item["link"]
    jalali     = _jalali_now()

    urgency_line = f"{urgency} خبر فوری\n" if urgency == "🔴" else (
                   f"{urgency} خبر مهم\n" if urgency == "🟠" else "")

    return (
        f"{urgency_line}"
        f"{emoji} {label}\n\n"
        f"📰 {title}\n\n"
        f"📝 {summary}\n\n"
        f"📅 {jalali}\n"
        f"📌 منبع: {source}\n"
        f"🔗 {link}"
    )
