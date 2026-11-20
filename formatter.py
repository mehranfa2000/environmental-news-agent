import jdatetime
import pytz
from datetime import datetime

# تایم‌زون ایران
IRAN_TZ = pytz.timezone("Asia/Tehran")

# نام روزهای هفته به فارسی
WEEKDAYS_FA = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنج‌شنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}

# سطح اهمیت به فارسی
URGENCY_LABEL = {
    "urgent": "🔴 فوری",
    "high":   "🟠 مهم",
    "medium": "🟡 متوسط",
    "low":    "🟢 عادی",
}


def get_jalali_now():
    """دریافت تاریخ و زمان کنونی به شمسی"""
    now_utc = datetime.now(pytz.utc)
    now_iran = now_utc.astimezone(IRAN_TZ)
    jdt = jdatetime.datetime.fromgregorian(datetime=now_iran)

    date_str = f"{jdt.year}/{jdt.month:02d}/{jdt.day:02d}"
    time_str = f"{jdt.hour:02d}:{jdt.minute:02d}"
    weekday_str = WEEKDAYS_FA.get(jdt.weekday(), "")

    return date_str, time_str, weekday_str


def format_telegram(item):
    """
    فرمت پیام برای تلگرام (HTML)
    """
    date_str, time_str, weekday = get_jalali_now()
    urgency_label = URGENCY_LABEL.get(item.get("urgency", "low"), "🟢 عادی")

    title = item.get("title", "")
    source = item.get("source", "نامشخص")
    group = item.get("group", "عمومی")
    cat_emoji = item.get("cat_emoji", "🌿")
    cat_label = item.get("cat_label", "محیط‌زیست")
    link = item.get("link", "")
    summary = item.get("summary", "")

    # خلاصه (حداکثر ۲۰۰ کاراکتر)
    if summary and len(summary) > 200:
        summary = summary[:200] + "..."

    # ساخت پیام HTML
    msg = f"{cat_emoji} <b>{title}</b>\n\n"

    if summary:
        msg += f"📝 {summary}\n\n"

    msg += f"📌 <b>منبع:</b> {source} ({group})\n"
    msg += f"🗂 <b>دسته:</b> {cat_label}\n"
    msg += f"⚡️ <b>اهمیت:</b> {urgency_label}\n"
    msg += f"📅 {weekday} {date_str} — ⏰ {time_str}\n\n"
    msg += f"🔗 <a href='{link}'>مطالعه خبر</a>"

    return msg


def format_bale(item):
    """
    فرمت پیام برای بله (متن ساده بدون HTML)
    """
    date_str, time_str, weekday = get_jalali_now()
    urgency_label = URGENCY_LABEL.get(item.get("urgency", "low"), "🟢 عادی")

    title = item.get("title", "")
    source = item.get("source", "نامشخص")
    group = item.get("group", "عمومی")
    cat_emoji = item.get("cat_emoji", "🌿")
    cat_label = item.get("cat_label", "محیط‌زیست")
    link = item.get("link", "")
    summary = item.get("summary", "")

    # خلاصه (حداکثر ۲۰۰ کاراکتر)
    if summary and len(summary) > 200:
        summary = summary[:200] + "..."

    # ساخت پیام ساده
    msg = f"{cat_emoji} {title}\n\n"

    if summary:
        msg += f"📝 {summary}\n\n"

    msg += f"📌 منبع: {source} ({group})\n"
    msg += f"🗂 دسته: {cat_label}\n"
    msg += f"⚡️ اهمیت: {urgency_label}\n"
    msg += f"📅 {weekday} {date_str} — ⏰ {time_str}\n\n"
    msg += f"🔗 {link}"

    return msg


def format_for_dashboard(item):
    """
    فرمت اطلاعات خبر برای ذخیره در news.json (داشبورد)
    """
    date_str, time_str, weekday = get_jalali_now()

    return {
        "id": item.get("id", ""),
        "title": item.get("title", ""),
        "link": item.get("link", ""),
        "source": item.get("source", "نامشخص"),
        "group": item.get("group", "عمومی"),
        "cat_key": item.get("cat_key", "pollution"),
        "cat_emoji": item.get("cat_emoji", "🌿"),
        "cat_label": item.get("cat_label", "محیط‌زیست"),
        "cat_color": item.get("cat_color", "#94a3b8"),
        "urgency": item.get("urgency", "low"),
        "date": date_str,
        "weekday": weekday,
        "time": time_str,
        "full": item.get("summary", ""),
        "score": item.get("score", 0),
    }
