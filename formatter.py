# ================================================================
#  formatter.py — قالب‌بندی پیام‌ها
# ================================================================
import re, logging
from html import unescape
from datetime import datetime
from typing import Optional
import pytz, jdatetime, requests
from config import TIMEZONE, FETCH_IMAGE, IMAGE_TIMEOUT

logger = logging.getLogger(__name__)
TZ = pytz.timezone(TIMEZONE)

WEEKDAYS = {0:"دوشنبه",1:"سه‌شنبه",2:"چهارشنبه",
            3:"پنج‌شنبه",4:"جمعه",5:"شنبه",6:"یکشنبه"}
MONTHS   = ["","فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
            "مهر","آبان","آذر","دی","بهمن","اسفند"]


def _now_jd():
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
    return jdatetime.datetime.fromgregorian(datetime=now)


def jalali_now():
    jd = _now_jd()
    return f"{WEEKDAYS[jd.weekday()]} {jd.day} {MONTHS[jd.month]} {jd.year} — {jd.strftime('%H:%M')}"


def jalali_parts():
    jd = _now_jd()
    return {
        "date":    f"{jd.day} {MONTHS[jd.month]} {jd.year}",
        "weekday": WEEKDAYS[jd.weekday()],
        "time":    jd.strftime("%H:%M"),
        "full":    f"{WEEKDAYS[jd.weekday()]} {jd.day} {MONTHS[jd.month]} {jd.year} ساعت {jd.strftime('%H:%M')}",
    }


def clean_html(text):
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>"," ",text)
    return re.sub(r"\s+"," ",text).strip()


def smart_summary(text, n=260):
    text = clean_html(text)
    if len(text) <= n: return text
    cut = text[:n]
    for sep in (".", "!", "?", "؟", "،"):
        p = cut.rfind(sep)
        if p > n//2: return cut[:p+1].strip()
    return cut.strip()+"…"


def _og_image(link):
    if not FETCH_IMAGE: return None
    try:
        r = requests.get(link, timeout=IMAGE_TIMEOUT,
                         headers={"User-Agent":"Mozilla/5.0"},
                         allow_redirects=True)
        if r.status_code != 200: return None
        m = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']',
            r.text, re.I)
        if m: return m.group(1)
        m = re.search(
            r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']',
            r.text, re.I)
        if m: return m.group(1)
    except Exception: pass
    return None


def format_telegram(item):
    u = item.get("urgency","")
    urgent_line = (f"{u} <b>خبر فوری</b>\n" if u=="🔴" else
                   f"{u} خبر مهم\n"           if u=="🟠" else "")
    text = (
        f"{urgent_line}"
        f"{item['category_emoji']} <b>{item['category_label']}</b>\n\n"
        f"📰 <b>{item['title_clean']}</b>\n\n"
        f"📝 {smart_summary(item.get('summary_clean',''))}\n\n"
        f"📅 {jalali_now()}\n"
        f"📌 {item['source']}\n"
        f"🔗 <a href=\"{item['link']}\">مشاهده خبر</a>"
    )
    img = item.get("image_url") or _og_image(item["link"])
    return {"text":text,"image_url":img,"parse_mode":"HTML"}


def format_bale(item):
    u = item.get("urgency","")
    urgent_line = (f"{u} خبر فوری\n" if u=="🔴" else
                   f"{u} خبر مهم\n"   if u=="🟠" else "")
    return (
        f"{urgent_line}"
        f"{item['category_emoji']} {item['category_label']}\n\n"
        f"📰 {item['title_clean']}\n\n"
        f"📝 {smart_summary(item.get('summary_clean',''),200)}\n\n"
        f"📅 {jalali_now()}\n"
        f"📌 {item['source']}\n"
        f"🔗 {item['link']}"
    )
