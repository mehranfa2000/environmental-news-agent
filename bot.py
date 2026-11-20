# ================================================================
#  🌿 Environmental News Agent — نسخه حرفه‌ای
#  ساخته‌شده برای: پایش و انتشار اخبار محیط‌زیست ایران
#  منابع: ایرنا، ایسنا، فارس، ایمنا، مهر، محیط‌زیست آنلاین
# ================================================================

import feedparser
import requests
import os
import json
import re
import hashlib
import logging
import time
from datetime import datetime
import pytz
import jdatetime
from html.parser import HTMLParser

# ──────────────────────────────────────────
#  تنظیم سیستم لاگ (ثبت رویدادها)
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────
#  ثابت‌های پروژه
# ──────────────────────────────────────────
MAX_HISTORY       = 1000   # حداکثر لینک‌های ذخیره‌شده برای جلوگیری از تکرار
MAX_ENTRIES       = 20     # تعداد خبر بررسی‌شده از هر منبع در هر اجرا
MIN_ENV_SCORE     = 2      # حداقل امتیاز برای انتشار خبر
SEND_DELAY        = 2      # تاخیر (ثانیه) بین ارسال هر خبر
RETRY_ATTEMPTS    = 3      # تعداد تلاش مجدد در صورت خطا
RETRY_DELAY       = 5      # تاخیر بین تلاش‌های مجدد (ثانیه)
SUMMARY_MAX_LEN   = 200    # حداکثر کاراکتر خلاصه خبر

# ──────────────────────────────────────────
#  منابع خبری (RSS Feeds)
# ──────────────────────────────────────────
SOURCES = {
    'ایرنا':              'https://www.irna.ir/rss/tp/20',
    'ایسنا':              'https://www.isna.ir/rss/tp/43',
    'فارس نیوز':          'https://www.farsnews.ir/rss/environment',
    'خبرگزاری مهر':       'https://www.mehrnews.com/rss/environment',
    'ایمنا':              'https://www.imna.ir/rss/environment',
    'محیط‌زیست آنلاین':  'https://www.moe.org.ir/fa/rss.xml',
}

# ──────────────────────────────────────────
#  کلیدواژه‌های محیط‌زیستی با وزن‌دهی
#  وزن ۳: کلیدواژه‌های بسیار تخصصی
#  وزن ۲: کلیدواژه‌های تخصصی
#  وزن ۱: کلیدواژه‌های عمومی‌تر
# ──────────────────────────────────────────
ENV_KEYWORDS_WEIGHTED = {

    # ═══ وزن ۳ (بسیار تخصصی) ═══
    'محیط زیست': 3, 'محیط‌زیست': 3, 'زیست‌محیطی': 3, 'زیست محیطی': 3,
    'سازمان حفاظت محیط زیست': 3, 'سازمان محیط زیست': 3,
    'تنوع زیستی': 3, 'اکوسیستم': 3, 'بیوسفر': 3, 'ژئوپارک': 3,
    'یوزپلنگ': 3, 'یوز آسیایی': 3, 'پلنگ ایرانی': 3,
    'دریاچه ارومیه': 3, 'تالاب هامون': 3, 'تالاب شادگان': 3,
    'هورالعظیم': 3, 'تالاب میانکاله': 3, 'تالاب انزلی': 3,
    'گاوخونی': 3, 'بختگان': 3, 'جازموریان': 3, 'پریشان': 3,
    'کنوانسیون رامسر': 3, 'کنوانسیون پاریس': 3,
    'کنوانسیون تنوع زیستی': 3, 'پروتکل کیوتو': 3,
    'ارزیابی زیست‌محیطی': 3, 'ارزیابی اثرات محیطی': 3,
    'گرمایش جهانی': 3, 'تغییر اقلیم': 3, 'تغییرات اقلیمی': 3,
    'گازهای گلخانه‌ای': 3, 'اثر گلخانه‌ای': 3,
    'انقراض': 3, 'گونه در خطر انقراض': 3, 'شکار غیرمجاز': 3,
    'صید غیرمجاز': 3, 'پلیس محیط زیست': 3, 'محیط‌بان': 3, 'محیطبان': 3,
    'آبخیزداری': 3, 'بیابان‌زدایی': 3, 'بیابانزدایی': 3,
    'ریزگرد': 3, 'گرد و غبار': 3, 'گردوغبار': 3,
    'آلودگی هوا': 3, 'آلودگی آب': 3, 'آلودگی خاک': 3,
    'شاخص کیفیت هوا': 3, 'ذرات معلق': 3, 'اسموگ': 3,
    'مه‌دود': 3, 'آلاینده': 3,
    'فرسایش خاک': 3, 'فرونشست': 3, 'بحران آب': 3,
    'حقابه': 3, 'حق‌آبه': 3, 'حقابه زیست‌محیطی': 3,
    'مدیریت پسماند': 3, 'بازیافت': 3, 'تفکیک زباله': 3,
    'انرژی تجدیدپذیر': 3, 'انرژی خورشیدی': 3, 'انرژی بادی': 3,
    'توسعه پایدار': 3, 'اقتصاد سبز': 3,
    'میکروپلاستیک': 3, 'نشت نفت': 3, 'لکه نفتی': 3,
    'آلودگی نفتی': 3, 'فلزات سنگین': 3,
    'پارک ملی': 3, 'منطقه حفاظت‌شده': 3, 'منطقه حفاظت شده': 3,
    'پناهگاه حیات وحش': 3, 'اثر طبیعی ملی': 3,
    'مانگرو': 3, 'جنگل حرا': 3, 'جنگل هیرکانی': 3,
    'لایه ازن': 3, 'سوراخ ازن': 3,
    'بوم‌شناسی': 3, 'اکولوژی': 3, 'زیست‌بوم': 3,
    'احیای طبیعت': 3, 'بازسازی اکولوژیک': 3,

    # ═══ وزن ۲ (تخصصی) ═══
    'جنگل': 2, 'جنگل‌زدایی': 2, 'جنگلکاری': 2, 'جنگل‌کاری': 2,
    'جنگلبانی': 2, 'جنگل‌بانی': 2, 'آتش‌سوزی جنگل': 2, 'حریق جنگل': 2,
    'قطع درخت': 2, 'نهالکاری': 2, 'تخریب جنگل': 2,
    'مراتع': 2, 'مرتع': 2, 'مرتعداری': 2, 'علفزار': 2,
    'چرای بی‌رویه': 2, 'چرای مفرط': 2,
    'بیابان': 2, 'کویر': 2, 'کویرزایی': 2, 'طوفان شن': 2,
    'تالاب': 2, 'دریاچه': 2, 'رودخانه': 2,
    'خشکسالی': 2, 'کم‌آبی': 2, 'سیل': 2, 'سیلاب': 2,
    'آب‌های زیرزمینی': 2, 'سفره آب': 2, 'سفره زیرزمینی': 2,
    'یخچال طبیعی': 2, 'ذوب یخ': 2, 'تنش آبی': 2,
    'حیات وحش': 2, 'حیات‌وحش': 2,
    'پلنگ': 2, 'خرس قهوه‌ای': 2, 'گرگ': 2, 'کفتار': 2, 'سیاه‌گوش': 2,
    'گوزن زرد': 2, 'آهو': 2, 'قوچ': 2, 'میش': 2, 'مرال': 2,
    'شوکا': 2, 'گورخر': 2, 'جبیر': 2, 'بز کوهی': 2,
    'عقاب': 2, 'شاهین': 2, 'کرکس': 2, 'هوبره': 2, 'فلامینگو': 2,
    'پلیکان': 2, 'درنا': 2, 'بالابان': 2, 'دلیجه': 2,
    'پرنده مهاجر': 2, 'مهاجرت پرندگان': 2, 'سرشماری پرندگان': 2,
    'لاک‌پشت': 2, 'سمندر': 2, 'دلفین': 2, 'نهنگ': 2,
    'زیستگاه': 2, 'تخریب زیستگاه': 2, 'کریدور حیات وحش': 2,
    'گونه گیاهی': 2, 'گیاه دارویی': 2, 'گیاه بومی': 2,
    'مرکز بازپروری': 2, 'مرکز تکثیر': 2, 'سرشماری حیات وحش': 2,
    'آلودگی': 2, 'آلایندگی': 2, 'مازوت': 2, 'فاضلاب': 2, 'پساب': 2,
    'تصفیه‌خانه': 2, 'باران اسیدی': 2, 'دود صنعتی': 2,
    'سرب': 2, 'جیوه': 2, 'آرسنیک': 2, 'کادمیوم': 2,
    'آفت‌کش': 2, 'حشره‌کش': 2, 'علف‌کش': 2, 'سموم': 2,
    'زباله': 2, 'پسماند': 2, 'لندفیل': 2, 'دفن زباله': 2,
    'زباله‌سوز': 2, 'پلاستیک': 2, 'نایلون': 2, 'یکبار مصرف': 2,
    'کمپوست': 2, 'بازچرخانی': 2, 'نخاله': 2, 'ضایعات': 2,
    'پسماند خطرناک': 2, 'پسماند بیمارستانی': 2, 'پسماند صنعتی': 2,
    'نیروگاه بادی': 2, 'پنل خورشیدی': 2, 'توربین بادی': 2,
    'انرژی پاک': 2, 'سوخت فسیلی': 2,
    'قانون محیط زیست': 2, 'لایحه محیط زیست': 2,
    'جریمه زیست‌محیطی': 2, 'تخلف زیست‌محیطی': 2,
    'جرم زیست‌محیطی': 2, 'مجوز زیست‌محیطی': 2,
    'فضای سبز': 2, 'پارک جنگلی': 2, 'کشاورزی ارگانیک': 2,
    'کشاورزی پایدار': 2, 'خودروی برقی': 2,
    'ردپای کربن': 2, 'انتشار کربن': 2, 'دی‌اکسید کربن': 2,
    'دریای خزر': 2, 'خلیج فارس': 2, 'دریای عمان': 2,
    'کارون': 2, 'زاینده‌رود': 2, 'هلیل‌رود': 2, 'ارس': 2,
    'بلوط': 2, 'زاگرس': 2, 'البرز': 2, 'جنگل ابر': 2,
    'منابع طبیعی': 2, 'سازمان جنگل‌ها': 2,
    'پوشش گیاهی': 2, 'تاج‌پوشش': 2, 'بذرپاشی': 2, 'بذرکاری': 2,
    'حفاظت خاک': 2, 'فرسایش': 2, 'رسوب': 2,
    'معدن غیرمجاز': 2, 'تخریب طبیعت': 2, 'تجاوز به طبیعت': 2,
    'زمین‌خواری': 2, 'تغییر کاربری': 2,
    'اکوتوریسم': 2, 'طبیعت‌گردی': 2, 'گردشگری طبیعت': 2,
    'ذخیره‌گاه زیستکره': 2, 'میراث طبیعی': 2,
    'آمایش سرزمین': 2, 'کاربری اراضی': 2,
    'گرده‌افشانی': 2, 'زنبور عسل': 2, 'پروانه': 2,
    'جلبک': 2, 'شکوفایی جلبکی': 2, 'مرجان': 2,
    'قنات': 2, 'آب شیرین‌کن': 2, 'آبیاری قطره‌ای': 2,
    'باروری ابر': 2, 'بارور کردن ابرها': 2,
    'شوری آب': 2, 'سدسازی': 2,
    'موج گرما': 2, 'افزایش دما': 2, 'بلایای اقلیمی': 2,
    'گردشگری پایدار': 2, 'معماری سبز': 2, 'ساختمان سبز': 2,
    'اقتصاد چرخشی': 2, 'مالیات سبز': 2,
    'سازمان مردم‌نهاد': 2, 'فعال محیط زیست': 2,
    'فاجعه زیست‌محیطی': 2, 'بحران محیط زیست': 2,
    'سواحل': 2, 'فرسایش ساحلی': 2,

    # ═══ وزن ۱ (عمومی‌تر ولی مرتبط) ═══
    'درخت': 1, 'نهال': 1, 'بوته': 1, 'درختچه': 1,
    'آب': 1, 'خاک': 1, 'هوا': 1,
    'پرنده': 1, 'پرندگان': 1, 'ماهی': 1, 'ماهیان': 1,
    'آبزی': 1, 'آبزیان': 1, 'جانوران': 1, 'حشره': 1,
    'گیاه': 1, 'علف': 1, 'مرغ': 1,
    'سد': 1, 'مخزن': 1, 'چشمه': 1, 'چاه': 1,
    'باغ': 1, 'مزرعه': 1, 'کشاورزی': 1,
    'آلودگی صوتی': 1, 'آلودگی نوری': 1,
    'رادیواکتیو': 1, 'پرتوزا': 1,
    'آب‌وهوا': 1, 'اقلیم': 1,
    'بهداشت محیط': 1, 'سلامت محیط': 1,
    'مه': 1, 'دود': 1, 'گاز': 1,
    'روز زمین': 1, 'روز محیط زیست': 1, 'هفته محیط زیست': 1,
    'سنجش از دور': 1, 'ماهواره': 1,
    'نیتروژن': 1, 'فسفر': 1, 'کود شیمیایی': 1,
    'ساحل': 1, 'جزیره': 1, 'خلیج': 1, 'تنگه': 1,
    'معدن': 1, 'استخراج': 1, 'حفاری': 1,
    'ساخت‌وساز غیرمجاز': 1, 'تصرف اراضی': 1,
    'دامداری': 1, 'کوچ': 1, 'عشایر': 1,
}

# ──────────────────────────────────────────
#  دسته‌بندی اخبار با کلیدواژه‌های اختصاصی
# ──────────────────────────────────────────
CATEGORIES = {
    '🌳 جنگل‌ها/مراتع/بیابان‌زدایی': [
        'جنگل', 'مراتع', 'مرتع', 'درخت', 'نهال', 'بیابان', 'کویر',
        'ریزگرد', 'گرد و غبار', 'بلوط', 'ارس', 'زاگرس', 'هیرکانی',
        'جنگل‌بان', 'محیطبان', 'آتش‌سوزی جنگل', 'بوته', 'شمشاد',
        'آبخیزداری', 'بذرپاشی', 'تاج‌پوشش', 'منابع طبیعی',
        'فرسایش خاک', 'کویرزایی', 'بیابان‌زدایی', 'جنگلکاری',
        'قطع درخت', 'تخریب جنگل', 'پوشش گیاهی',
    ],
    '🐾 حیات‌وحش/تنوع زیستی': [
        'حیات وحش', 'حیات‌وحش', 'انقراض', 'تنوع زیستی',
        'شکار غیرمجاز', 'صید غیرمجاز', 'پلنگ', 'یوزپلنگ', 'یوز',
        'خرس', 'گوزن', 'آهو', 'قوچ', 'میش', 'مرال', 'گورخر',
        'عقاب', 'شاهین', 'فلامینگو', 'پلیکان', 'هوبره', 'درنا',
        'پرنده مهاجر', 'خزنده', 'لاک‌پشت', 'سمندر', 'دلفین',
        'زیستگاه', 'گونه در خطر', 'مرکز بازپروری', 'سرشماری',
        'گونه گیاهی', 'گیاه بومی', 'جانوران', 'کریدور حیات وحش',
    ],
    '💧 منابع آبی/تالاب‌ها': [
        'تالاب', 'دریاچه', 'رودخانه', 'خشکسالی', 'کم‌آبی',
        'سفره آب', 'فرونشست', 'بحران آب', 'تنش آبی',
        'دریاچه ارومیه', 'هامون', 'گاوخونی', 'بختگان',
        'هورالعظیم', 'شادگان', 'جازموریان', 'انزلی',
        'حقابه', 'حق‌آبه', 'افت سطح آب', 'آب‌های زیرزمینی',
        'سیل', 'سیلاب', 'یخچال طبیعی', 'ذوب یخ',
        'قنات', 'کارون', 'زاینده‌رود',
    ],
    '🏭 آلودگی محیط زیست': [
        'آلودگی', 'آلاینده', 'مازوت', 'فاضلاب', 'پساب',
        'ذرات معلق', 'شاخص کیفیت هوا', 'اسموگ', 'مه‌دود',
        'نشت نفت', 'لکه نفتی', 'فلزات سنگین', 'سرب', 'جیوه',
        'آرسنیک', 'میکروپلاستیک', 'باران اسیدی',
        'آلودگی هوا', 'آلودگی آب', 'آلودگی خاک',
        'سموم', 'آفت‌کش', 'آلودگی نفتی', 'دود صنعتی',
    ],
    '🏔️ مناطق حفاظت‌شده/پارک‌های ملی': [
        'حفاظت‌شده', 'حفاظت شده', 'پارک ملی', 'اثر طبیعی ملی',
        'محیط‌بان', 'محیطبان', 'پناهگاه حیات وحش',
        'ژئوپارک', 'ذخیره‌گاه زیستکره', 'مناطق بیوسفر',
        'جنگل ابر', 'مانگرو', 'جنگل حرا', 'اکوتوریسم',
        'پلیس محیط زیست', 'میراث طبیعی',
    ],
    '♻️ پسماند/بازیافت': [
        'زباله', 'پسماند', 'بازیافت', 'تفکیک زباله',
        'دفن زباله', 'لندفیل', 'زباله‌سوز', 'پلاستیک', 'نایلون',
        'یکبار مصرف', 'کمپوست', 'مدیریت پسماند',
        'پسماند خطرناک', 'نخاله', 'ضایعات', 'بازچرخانی',
        'پسماند الکترونیکی', 'میکروپلاستیک',
    ],
    '⚖️ قوانین/سیاست‌های محیط زیستی': [
        'سازمان محیط زیست', 'سازمان حفاظت محیط زیست',
        'قانون محیط زیست', 'لایحه محیط زیست',
        'کنوانسیون رامسر', 'کنوانسیون پاریس', 'کنوانسیون تنوع زیستی',
        'ارزیابی زیست‌محیطی', 'جریمه زیست‌محیطی',
        'تخلف زیست‌محیطی', 'پلیس محیط زیست',
        'مجوز زیست‌محیطی', 'دادگاه محیط زیست',
        'توسعه پایدار', 'اقتصاد سبز', 'مالیات سبز',
    ],
    '🌡️ تغییر اقلیم/انرژی': [
        'تغییر اقلیم', 'تغییرات اقلیمی', 'گرمایش جهانی',
        'گازهای گلخانه‌ای', 'اثر گلخانه‌ای', 'ردپای کربن',
        'انرژی تجدیدپذیر', 'انرژی خورشیدی', 'انرژی بادی',
        'نیروگاه بادی', 'پنل خورشیدی', 'توربین بادی',
        'سوخت فسیلی', 'لایه ازن', 'موج گرما',
        'خودروی برقی', 'انرژی پاک',
    ],
}

# ──────────────────────────────────────────
#  کلاس پاک‌کننده HTML
# ──────────────────────────────────────────
class HTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts)

def clean_html(raw_html: str) -> str:
    """حذف تگ‌های HTML و فاصله‌های اضافی"""
    if not raw_html:
        return ''
    parser = HTMLCleaner()
    try:
        parser.feed(raw_html)
        text = parser.get_text()
    except Exception:
        text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def make_summary(raw_text: str, max_len: int = SUMMARY_MAX_LEN) -> str:
    """ساخت خلاصه هوشمند از متن خبر"""
    text = clean_html(raw_text)
    if not text:
        return ''
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    last_space = cut.rfind(' ')
    if last_space > max_len * 0.6:
        cut = cut[:last_space]
    return cut + '…'

# ──────────────────────────────────────────
#  توابع امتیازدهی و دسته‌بندی
# ──────────────────────────────────────────
def calculate_env_score(title: str, summary: str) -> int:
    """محاسبه امتیاز زیست‌محیطی خبر بر اساس وزن کلیدواژه‌ها"""
    text = title + ' ' + summary
    score = 0
    for keyword, weight in ENV_KEYWORDS_WEIGHTED.items():
        if keyword in text:
            score += weight
    return score

def get_category(title: str, summary: str) -> str:
    """تعیین دسته‌بندی بر اساس بیشترین تطابق"""
    text = title + ' ' + summary
    best_cat = '🌍 سایر اخبار محیط زیست'
    max_hits = 0
    for cat, keywords in CATEGORIES.items():
        hits = sum(weight for kw, weight in ENV_KEYWORDS_WEIGHTED.items()
                   if kw in keywords and kw in text)
        if hits > max_hits:
            max_hits = hits
            best_cat = cat
    return best_cat

def make_content_hash(title: str, link: str) -> str:
    """ساخت هش یکتا از عنوان و لینک"""
    content = (title + link).encode('utf-8')
    return hashlib.md5(content).hexdigest()

# ──────────────────────────────────────────
#  توابع ارسال پیام
# ──────────────────────────────────────────
def send_request_with_retry(url: str, payload: dict, label: str) -> bool:
    """ارسال درخواست با مکانیزم Retry"""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                return True
            else:
                log.warning(f"[{label}] تلاش {attempt}: خطای {resp.status_code} — {resp.text[:100]}")
        except requests.exceptions.RequestException as e:
            log.warning(f"[{label}] تلاش {attempt}: خطای شبکه — {e}")
        if attempt < RETRY_ATTEMPTS:
            time.sleep(RETRY_DELAY)
    return False

def send_to_telegram(text: str) -> bool:
    token   = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHANNEL_ID')
    if not token or not chat_id:
        log.error("توکن یا آیدی تلگرام یافت نشد.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                "disable_web_page_preview": False}
    return send_request_with_retry(url, payload, "Telegram")

def send_to_bale(text: str) -> bool:
    token   = os.getenv('BALE_BOT_TOKEN')
    chat_id = os.getenv('BALE_CHANNEL_ID')
    if not token or not chat_id:
        log.error("توکن یا آیدی بله یافت نشد.")
        return False
    clean_text = re.sub(r'<[^>]+>', '', text)  # بله از HTML ساده پشتیبانی می‌کند
    url = f"https://tapi.bale.ai/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": clean_text}
    return send_request_with_retry(url, payload, "Bale")

def format_message(title: str, summary: str, link: str,
                   source: str, category: str,
                   now_tehran: datetime) -> str:
    """فرمت‌بندی حرفه‌ای پیام"""
    jdt = jdatetime.datetime.fromgregorian(datetime=now_tehran)
    jalali_date  = jdt.strftime('%Y/%m/%d')
    jalali_time  = jdt.strftime('%H:%M')

    sep = '┄' * 18
    msg = (
        f"{category}\n"
        f"{sep}\n"
        f"<b>{title}</b>\n\n"
        f"📝 {summary}\n\n"
        f"{sep}\n"
        f"📌 منبع: {source}\n"
        f"🕒 ساعت: {jalali_time}\n"
        f"📅 تاریخ: {jalali_date}\n\n"
        f"🔗 {link}"
    )
    return msg

# ──────────────────────────────────────────
#  بارگذاری و ذخیره داده‌ها
# ──────────────────────────────────────────
def load_json(filepath: str, default) -> any:
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"خطا در خواندن {filepath}: {e}")
    return default

def save_json(filepath: str, data: any) -> None:
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"خطا در ذخیره {filepath}: {e}")

# ──────────────────────────────────────────
#  تابع اصلی
# ──────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("🌿 ایجنت اخبار محیط‌زیست — شروع اجرا")
    log.info("=" * 50)

    # بارگذاری دیتابیس تاریخچه (هش‌های ارسال‌شده)
    history: list = load_json('history.json', [])
    history_set   = set(history)

    # بارگذاری آمار
    stats: dict = load_json('stats.json', {
        "total_sent": 0,
        "total_checked": 0,
        "total_filtered_irrelevant": 0,
        "total_filtered_duplicate": 0,
        "last_run": "",
        "by_source": {},
        "by_category": {},
        "run_count": 0,
    })

    tehran_tz = pytz.timezone('Asia/Tehran')
    now_tehran = datetime.now(tehran_tz)
    stats["last_run"] = now_tehran.strftime('%Y-%m-%d %H:%M:%S')
    stats["run_count"] = stats.get("run_count", 0) + 1

    new_hashes  = []
    total_sent  = 0
    total_irrel = 0
    total_dupl  = 0

    for source_name, feed_url in SOURCES.items():
        log.info(f"📡 در حال دریافت اخبار از: {source_name}")
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries[:MAX_ENTRIES]
            log.info(f"   ← {len(entries)} خبر دریافت شد")
        except Exception as e:
            log.error(f"   ✗ خطا در خواندن {source_name}: {e}")
            continue

        for entry in entries:
            stats["total_checked"] = stats.get("total_checked", 0) + 1

            title   = clean_html(entry.get('title',   ''))
            summary = clean_html(entry.get('summary', ''))
            link    = entry.get('link', '')

            if not title or not link:
                continue

            # بررسی تکراری بودن
            content_hash = make_content_hash(title, link)
            if content_hash in history_set:
                total_dupl += 1
                stats["total_filtered_duplicate"] = stats.get("total_filtered_duplicate", 0) + 1
                continue

            # بررسی امتیاز زیست‌محیطی
            score = calculate_env_score(title, summary)
            if score < MIN_ENV_SCORE:
                total_irrel += 1
                stats["total_filtered_irrelevant"] = stats.get("total_filtered_irrelevant", 0) + 1
                log.info(f"   ✗ فیلتر شد (امتیاز={score}): {title[:50]}")
                continue

            # تعیین دسته‌بندی
            category = get_category(title, summary)

            # ساخت خلاصه هوشمند
            short_summary = make_summary(summary, SUMMARY_MAX_LEN)

            # فرمت‌بندی و ارسال
            message = format_message(
                title, short_summary, link,
                source_name, category, now_tehran
            )

            tg_ok   = send_to_telegram(message)
            time.sleep(SEND_DELAY)
            bale_ok = send_to_bale(message)

            if tg_ok or bale_ok:
                history_set.add(content_hash)
                new_hashes.append(content_hash)
                total_sent += 1
                stats["total_sent"] = stats.get("total_sent", 0) + 1
                stats["by_source"][source_name] = stats.get("by_source", {}).get(source_name, 0) + 1
                stats["by_category"][category]  = stats.get("by_category", {}).get(category, 0) + 1
                log.info(f"   ✓ ارسال شد (امتیاز={score}): {title[:50]}")

    # ──── خلاصه اجرا ────
    log.info("=" * 50)
    log.info(f"✅ ارسال‌شده:    {total_sent}")
    log.info(f"🔁 تکراری:      {total_dupl}")
    log.info(f"🚫 بی‌ربط:      {total_irrel}")
    log.info("=" * 50)

    # ذخیره تاریخچه (حداکثر MAX_HISTORY هش آخر)
    full_history = list(history_set)
    save_json('history.json', full_history[-MAX_HISTORY:])
    save_json('stats.json', stats)

    log.info("💾 داده‌ها ذخیره شدند. اجرا پایان یافت.")

if __name__ == "__main__":
    main()
