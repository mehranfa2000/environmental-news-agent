import feedparser
import requests
import os
import json
from datetime import datetime
import pytz

# تنظیمات منابع خبری (RSS Feeds)
SOURCES = {
    'ایسنا': 'https://www.isna.ir/rss/tp/43',
    'ایرنا': 'https://www.irna.ir/rss/tp/20',
    'فارس': 'https://www.farsnews.ir/rss/environment'
}

# دسته‌بندی‌ها و کلمات کلیدی
CATEGORIES = {
    '🌳 جنگل‌ها/مراتع/بیابان‌زدایی': ['جنگل', 'مراتع', 'درخت', 'قطع درخت', 'بیابان', 'ریزگرد', 'نهال'],
    '🐾 حیات‌وحش/تنوع زیستی': ['حیات وحش', 'انقراض', 'حیوانات', 'شکار', 'پلنگ', 'یوزپلنگ', 'گونه گیاهی'],
    '💧 منابع آبی/تالاب‌ها': ['آب', 'تالاب', 'دریاچه', 'خشکسالی', 'رودخانه', 'سد', 'کم‌آبی'],
    '🏭 آلودگی محیط زیست': ['آلودگی', 'هوا', 'آلاینده', 'مازوت', 'سموم', 'فاضلاب', 'ریزگرد'],
    '🏔️ مناطق حفاظت‌شده/پارک‌های ملی': ['حفاظت شده', 'پارک ملی', 'محیطبان', 'محیط‌بان', 'شکار ممنوع'],
    '♻️ پسماند/بازیافت': ['زباله', 'پسماند', 'بازیافت', 'مدیریت پسماند', 'تفکیک'],
    '⚖️ قوانین/سیاست‌های محیط زیستی': ['مجلس', 'لایحه', 'قانون', 'کنوانسیون', 'سازمان محیط زیست', 'بودجه']
}

def get_category(title, summary):
    text = (title + " " + summary).lower()
    for cat, keywords in CATEGORIES.items():
        if any(key in text for key in keywords):
            return cat
    return "🌍 سایر اخبار محیط زیست"

def send_to_messengers(text):
    # ارسال به تلگرام
    tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.getenv('TELEGRAM_CHANNEL_ID')
    if tg_token and tg_chat_id:
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        requests.post(url, json={"chat_id": tg_chat_id, "text": text, "parse_mode": "HTML"})

    # ارسال به بله
    bale_token = os.getenv('BALE_BOT_TOKEN')
    bale_chat_id = os.getenv('BALE_CHANNEL_ID')
    if bale_token and bale_chat_id:
        url = f"https://tapi.bale.ai/bot{bale_token}/sendMessage"
        requests.post(url, json={"chat_id": bale_chat_id, "text": text})

def main():
    # خواندن دیتابیس ساده برای جلوگیری از ارسال تکراری
    db_file = 'history.json'
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            sent_links = json.load(f)
    else:
        sent_links = []

    tehran_tz = pytz.timezone('Asia/Tehran')
    new_links = []
    
    for source_name, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]: # بررسی ۵ خبر آخر هر منبع
            if entry.link not in sent_links:
                category = get_category(entry.title, entry.summary)
                now = datetime.now(tehran_tz)
                
                message = (
                    f"{category}\n\n"
                    f"<b>{entry.title}</b>\n\n"
                    f"🔹 منبع: {source_name}\n"
                    f"🕒 ساعت: {now.strftime('%H:%M')}\n"
                    f"📅 تاریخ: {now.strftime('%Y/%m/%d')}\n\n"
                    f"🔗 {entry.link}"
                )
                
                send_to_messengers(message)
                sent_links.append(entry.link)
                new_links.append(entry.link)

    # ذخیره لینک‌های ارسال شده (حداکثر ۱۰۰ مورد آخر)
    with open(db_file, 'w') as f:
        json.dump(sent_links[-100:], f)

if __name__ == "__main__":
    main()
