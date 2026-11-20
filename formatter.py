# ================================================================
#  📐 قالب‌بندی حرفه‌ای پیام‌های خبری
# ================================================================

import re
from html.parser import HTMLParser
from datetime import datetime
import jdatetime

SUMMARY_MAX_LEN = 220

JALALI_MONTHS = {
    1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
    4: 'تیر',     5: 'مرداد',    6: 'شهریور',
    7: 'مهر',     8: 'آبان',     9: 'آذر',
    10: 'دی',     11: 'بهمن',    12: 'اسفند',
}

class HTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return ' '.join(self._parts)

def clean_html(raw: str) -> str:
    """پاک‌سازی کامل HTML و فاصله‌های اضافه"""
    if not raw:
        return ''
    parser = HTMLCleaner()
    try:
        parser.feed(raw)
        text = parser.get_text()
    except Exception:
        text = re.sub(r'<[^>]+>', ' ', raw)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def smart_summary(raw_text: str, max_len: int = SUMMARY_MAX_LEN) -> str:
    """ساخت خلاصه هوشمند — قطع در آخرین جمله کامل"""
    text = clean_html(raw_text)
    if not text or len(text) < 20:
        return ''
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    # قطع در آخرین علامت نگارشی
    for punct in ['؟', '!', '.', '،']:
        idx = cut.rfind(punct)
        if idx > max_len * 0.6:
            return cut[:idx + 1]
    # قطع در آخرین فاصله
    idx = cut.rfind(' ')
    if idx > max_len * 0.6:
        return cut[:idx] + '…'
    return cut + '…'

def persian_datetime(dt: datetime) -> tuple[str, str]:
    """تبدیل تاریخ میلادی به شمسی کامل"""
    jdt = jdatetime.datetime.fromgregorian(datetime=dt)
    day     = jdt.day
    month   = JALALI_MONTHS[jdt.month]
    year    = jdt.year
    hour    = jdt.strftime('%H:%M')
    weekday_map = {
        0: 'دوشنبه', 1: 'سه‌شنبه', 2: 'چهارشنبه',
        3: 'پنج‌شنبه', 4: 'جمعه', 5: 'شنبه', 6: 'یکشنبه',
    }
    weekday = weekday_map[jdt.weekday()]
    date_str = f"{weekday} {day} {month} {year}"
    return date_str, hour

def format_telegram(title: str, summary: str, link: str,
                    source: str, category: str,
                    score: int, dt: datetime) -> str:
    """فرمت پیام برای تلگرام (پشتیبانی HTML)"""
    date_str, hour = persian_datetime(dt)
    sep = '┄' * 20
    
    summary_block = f"\n📝 <i>{summary}</i>\n" if summary else ""

    msg = (
        f"{category}\n"
        f"{sep}\n"
        f"<b>{title}</b>\n"
        f"{summary_block}"
        f"{sep}\n"
        f"📌 <b>منبع:</b> {source}\n"
        f"📅 <b>تاریخ:</b> {date_str}\n"
        f"🕒 <b>ساعت:</b> {hour}\n\n"
        f"🔗 {link}"
    )
    return msg

def format_bale(title: str, summary: str, link: str,
                source: str, category: str,
                score: int, dt: datetime) -> str:
    """فرمت پیام برای بله (بدون HTML پیچیده)"""
    date_str, hour = persian_datetime(dt)
    sep = '─' * 22

    summary_block = f"\n📝 {summary}\n" if summary else ""

    msg = (
        f"{category}\n"
        f"{sep}\n"
        f"{title}\n"
        f"{summary_block}"
        f"{sep}\n"
        f"📌 منبع: {source}\n"
        f"📅 تاریخ: {date_str}\n"
        f"🕒 ساعت: {hour}\n\n"
        f"🔗 {link}"
    )
    return msg
