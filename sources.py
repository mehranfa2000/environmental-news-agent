# ============================================================
#  sources.py  —  ۱۲۰+ منبع RSS محیط زیستی
#  ساختار: (نام_نمایشی, آدرس_RSS, گروه)
# ============================================================

SOURCES = [

    # ══════════════════════════════════════════════════════
    #  🇮🇷  ایرانی — رسمی
    # ══════════════════════════════════════════════════════
    ("ایرنا - محیط زیست",       "https://www.irna.ir/rss/environment.xml",                    "ایرانی_رسمی"),
    ("ایسنا - محیط زیست",       "https://www.isna.ir/rss/tp/8",                               "ایرانی_رسمی"),
    ("مهر - محیط زیست",         "https://www.mehrnews.com/rss/environment",                   "ایرانی_رسمی"),
    ("تسنیم - محیط زیست",       "https://www.tasnimnews.com/fa/rss/feed/0/8/0",               "ایرانی_رسمی"),
    ("فارس - محیط زیست",        "https://www.farsnews.ir/rss/environment",                    "ایرانی_رسمی"),
    ("صدا و سیما - محیط زیست",  "https://www.iribnews.ir/fa/rss/environment",                 "ایرانی_رسمی"),
    ("ایبنا - محیط زیست",       "https://www.ibna.ir/rss/environment",                        "ایرانی_رسمی"),
    ("شبستان - محیط زیست",      "https://shabestan.ir/rss/environment",                       "ایرانی_رسمی"),
    ("شفقنا - محیط زیست",       "https://fa.shafaqna.com/rss/environment",                    "ایرانی_رسمی"),
    ("پانا - محیط زیست",        "https://www.pana.ir/rss/environment",                        "ایرانی_رسمی"),
    ("ایکنا - محیط زیست",       "https://iqna.ir/fa/rss/environment",                         "ایرانی_رسمی"),
    ("برنا - محیط زیست",        "https://www.borna.news/rss/environment",                     "ایرانی_رسمی"),

    # ══════════════════════════════════════════════════════
    #  🇮🇷  ایرانی — تخصصی محیط زیست
    # ══════════════════════════════════════════════════════
    ("محیط‌بان",                 "https://www.mohitban.com/feed",                              "ایرانی_تخصصی"),
    ("طبیعت نیوز",              "https://www.tabiatNews.com/feed",                             "ایرانی_تخصصی"),
    ("سبزپرس",                  "https://www.sabzpress.com/feed",                              "ایرانی_تخصصی"),
    ("اکوایران",                "https://www.eco-iran.ir/feed",                               "ایرانی_تخصصی"),
    ("محیط زیست آنلاین",        "https://www.environmentonline.ir/feed",                      "ایرانی_تخصصی"),
    ("سازمان محیط زیست",        "https://www.doe.ir/portal/home/?rss/637871",                 "ایرانی_تخصصی"),
    ("انرژی امروز",             "https://www.energytoday.ir/feed",                            "ایرانی_تخصصی"),
    ("اقتصاد سبز",              "https://www.greeneconomy.ir/feed",                           "ایرانی_تخصصی"),
    ("پایگاه اطلاع‌رسانی آب",   "https://www.waterweb.ir/feed",                               "ایرانی_تخصصی"),
    ("ایران واتر",              "https://www.iranwater.ir/feed",                              "ایرانی_تخصصی"),
    ("محیط زیست خبر",          "https://www.environmentnews.ir/feed",                        "ایرانی_تخصصی"),
    ("جنگل و مرتع",             "https://www.frw.ir/rss",                                     "ایرانی_تخصصی"),

    # ══════════════════════════════════════════════════════
    #  🇮🇷  ایرانی — عمومی (با کارایی محیط زیستی)
    # ══════════════════════════════════════════════════════
    ("خبرآنلاین - محیط زیست",   "https://www.khabaronline.ir/rss/environment",                "ایرانی_عمومی"),
    ("عصر ایران - محیط زیست",   "https://www.asriran.com/rss/environment",                    "ایرانی_عمومی"),
    ("تابناک - محیط زیست",      "https://www.tabnak.ir/fa/rss/environment",                   "ایرانی_عمومی"),
    ("الف - محیط زیست",         "https://www.alef.ir/rss/environment",                        "ایرانی_عمومی"),
    ("خبر فوری - محیط زیست",    "https://www.khabarfoori.com/rss/environment",                "ایرانی_عمومی"),
    ("دیده‌بان ایران",           "https://www.didbaniran.ir/rss/environment",                  "ایرانی_عمومی"),
    ("آرمان ملی",               "https://www.armandaily.ir/rss/environment",                  "ایرانی_عمومی"),
    ("روزنامه شرق",             "https://www.sharghdaily.com/rss/environment",                "ایرانی_عمومی"),
    ("ایران اکونومیست",         "https://iraneconomist.com/rss/environment",                  "ایرانی_عمومی"),

    # ══════════════════════════════════════════════════════
    #  🌍  بین‌المللی — رسانه‌های اصلی
    # ══════════════════════════════════════════════════════
    ("BBC - Environment",        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "بین‌المللی_رسانه"),
    ("The Guardian - Environment","https://www.theguardian.com/environment/rss",               "بین‌المللی_رسانه"),
    ("Reuters - Environment",    "https://feeds.reuters.com/reuters/environment",              "بین‌المللی_رسانه"),
    ("Al Jazeera - Environment", "https://www.aljazeera.com/xml/rss/all.xml",                 "بین‌المللی_رسانه"),
    ("DW - Environment",         "https://rss.dw.com/rdf/rss-en-environment",                 "بین‌المللی_رسانه"),
    ("CNN - Climate",            "https://rss.cnn.com/rss/edition.rss",                       "بین‌المللی_رسانه"),
    ("NYT - Climate",            "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",  "بین‌المللی_رسانه"),
    ("Washington Post - Climate","https://feeds.washingtonpost.com/rss/national/environment", "بین‌المللی_رسانه"),
    ("France 24 - Environment",  "https://www.france24.com/en/environment/rss",               "بین‌المللی_رسانه"),
    ("Sky News - Environment",   "https://feeds.skynews.com/feeds/rss/science.xml",           "بین‌المللی_رسانه"),
    ("The Independent - Env",    "https://www.independent.co.uk/environment/rss",             "بین‌المللی_رسانه"),
    ("The Hill - Energy",        "https://thehill.com/policy/energy-environment/feed/",       "بین‌المللی_رسانه"),
    ("Politico - Climate",       "https://rss.politico.com/politics-news.xml",                "بین‌المللی_رسانه"),

    # ══════════════════════════════════════════════════════
    #  🌿  بین‌المللی — تخصصی محیط زیست
    # ══════════════════════════════════════════════════════
    ("Mongabay",                 "https://news.mongabay.com/feed/",                           "بین‌المللی_تخصصی"),
    ("Yale Environment 360",     "https://e360.yale.edu/feed",                                "بین‌المللی_تخصصی"),
    ("Carbon Brief",             "https://www.carbonbrief.org/feed",                          "بین‌المللی_تخصصی"),
    ("Inside Climate News",      "https://insideclimatenews.org/feed",                        "بین‌المللی_تخصصی"),
    ("Climate Home News",        "https://www.climatechangenews.com/feed",                    "بین‌المللی_تخصصی"),
    ("EcoWatch",                 "https://www.ecowatch.com/feeds/latest.rss",                 "بین‌المللی_تخصصی"),
    ("Environmental Defense Fund","https://www.edf.org/rss.xml",                             "بین‌المللی_تخصصی"),
    ("Treehugger",               "https://www.treehugger.com/feeds/all",                      "بین‌المللی_تخصصی"),
    ("Grist",                    "https://grist.org/feed/",                                   "بین‌المللی_تخصصی"),
    ("DeSmog",                   "https://www.desmog.com/feed/",                              "بین‌المللی_تخصصی"),
    ("Clean Technica",           "https://cleantechnica.com/feed/",                           "بین‌المللی_تخصصی"),
    ("Renew Economy",            "https://reneweconomy.com.au/feed/",                         "بین‌المللی_تخصصی"),
    ("PV Magazine",              "https://www.pv-magazine.com/feed/",                         "بین‌المللی_تخصصی"),
    ("Wind Power Monthly",       "https://www.windpowermonthly.com/rss-feeds",                "بین‌المللی_تخصصی"),
    ("Hydropower & Dams",        "https://www.hydropower-dams.com/feed",                      "بین‌المللی_تخصصی"),
    ("Global Water Forum",       "https://globalwaterforum.org/feed/",                        "بین‌المللی_تخصصی"),
    ("Water World",              "https://www.waterworld.com/rss",                            "بین‌المللی_تخصصی"),
    ("Wildfire Today",           "https://wildfiretoday.com/feed/",                           "بین‌المللی_تخصصی"),
    ("Mongabay - Forests",       "https://news.mongabay.com/list/forests/feed/",              "بین‌المللی_تخصصی"),
    ("Mongabay - Wildlife",      "https://news.mongabay.com/list/wildlife/feed/",             "بین‌المللی_تخصصی"),

    # ══════════════════════════════════════════════════════
    #  🏛️  سازمان‌های بین‌المللی
    # ══════════════════════════════════════════════════════
    ("UNEP - News",              "https://www.unep.org/news-and-stories/news/rss.xml",        "سازمان‌بین‌المللی"),
    ("WWF - News",               "https://www.worldwildlife.org/press-releases.rss",          "سازمان‌بین‌المللی"),
    ("IUCN - News",              "https://www.iucn.org/news/rss.xml",                         "سازمان‌بین‌المللی"),
    ("IPCC - News",              "https://www.ipcc.ch/feed/",                                 "سازمان‌بین‌المللی"),
    ("NASA - Climate",           "https://climate.nasa.gov/news/rss.xml",                     "سازمان‌بین‌المللی"),
    ("NOAA - News",              "https://www.noaa.gov/news-release/rss.xml",                 "سازمان‌بین‌المللی"),
    ("FAO - Environment",        "https://www.fao.org/news/rss-feed/en/",                     "سازمان‌بین‌المللی"),
    ("WHO - Environment",        "https://www.who.int/rss-feeds/news-english.xml",            "سازمان‌بین‌المللی"),
    ("World Bank - Environment", "https://feeds.worldbank.org/worldbank/environment",         "سازمان‌بین‌المللی"),
    ("UNDP - Climate",           "https://www.undp.org/rss.xml",                              "سازمان‌بین‌المللی"),
    ("Greenpeace International", "https://www.greenpeace.org/international/feed/news/",       "سازمان‌بین‌المللی"),
    ("Conservation International","https://www.conservation.org/feed",                        "سازمان‌بین‌المللی"),
    ("Wildlife Conservation Soc.","https://www.wcs.org/rss",                                 "سازمان‌بین‌المللی"),
    ("Ramsar Convention",        "https://www.ramsar.org/rss.xml",                            "سازمان‌بین‌المللی"),
    ("CITES",                    "https://cites.org/eng/news/rss.xml",                        "سازمان‌بین‌المللی"),

    # ══════════════════════════════════════════════════════
    #  📰  منابع عربی و آسیایی
    # ══════════════════════════════════════════════════════
    ("العربی الجدید - بیئة",    "https://www.alaraby.co.uk/rss/environment",                 "منطقه‌ای_عربی_آسیایی"),
    ("الجزیره - بیئة",          "https://www.aljazeera.net/environment/rss",                 "منطقه‌ای_عربی_آسیایی"),
    ("Middle East Eye - Env",    "https://www.middleeasteye.net/rss/environment",             "منطقه‌ای_عربی_آسیایی"),
    ("Arab News - Environment",  "https://www.arabnews.com/taxonomy/term/9/rss",              "منطقه‌ای_عربی_آسیایی"),
    ("Japan Times - Environment","https://www.japantimes.co.jp/rss/environment",              "منطقه‌ای_عربی_آسیایی"),
    ("South China Morning Post", "https://www.scmp.com/rss/91/feed",                         "منطقه‌ای_عربی_آسیایی"),
    ("Times of India - Env",     "https://timesofindia.indiatimes.com/rss/environment",      "منطقه‌ای_عربی_آسیایی"),
    ("The Hindu - Environment",  "https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss", "منطقه‌ای_عربی_آسیایی"),
    ("Eco Business (Asia)",      "https://www.eco-business.com/feed/",                        "منطقه‌ای_عربی_آسیایی"),
    ("Climate Tracker",          "https://climatetracker.org/feed/",                          "منطقه‌ای_عربی_آسیایی"),

    # ══════════════════════════════════════════════════════
    #  🔬  نشریات علمی
    # ══════════════════════════════════════════════════════
    ("Nature - Climate",         "https://www.nature.com/nclimate.rss",                       "نشریه_علمی"),
    ("Nature - Sustainability",  "https://www.nature.com/natsustain.rss",                     "نشریه_علمی"),
    ("Science - Environment",    "https://www.science.org/rss/news_current.xml",              "نشریه_علمی"),
    ("Environ. Research Letters","https://iopscience.iop.org/journal/rss/1748-9326",          "نشریه_علمی"),
    ("Environ. Science & Tech.", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=esthag", "نشریه_علمی"),
    ("Global Change Biology",    "https://onlinelibrary.wiley.com/feed/13652486/most-recent", "نشریه_علمی"),
    ("Biological Conservation",  "https://www.journals.elsevier.com/biological-conservation/rss", "نشریه_علمی"),
    ("Water Research",           "https://www.journals.elsevier.com/water-research/rss",      "نشریه_علمی"),
    ("Forest Ecology & Mgmt",    "https://www.journals.elsevier.com/forest-ecology-and-management/rss", "نشریه_علمی"),
    ("ScienceDaily - Env",       "https://www.sciencedaily.com/rss/earth_climate.xml",        "نشریه_علمی"),
    ("Phys.org - Environment",   "https://phys.org/rss-feed/earth-news/environment/",         "نشریه_علمی"),

]

# ── گروه‌بندی برای آمار ───────────────────────────────────────
GROUP_LABELS = {
    "ایرانی_رسمی":           "🇮🇷 ایرانی — رسمی",
    "ایرانی_تخصصی":          "🇮🇷 ایرانی — تخصصی",
    "ایرانی_عمومی":          "🇮🇷 ایرانی — عمومی",
    "بین‌المللی_رسانه":      "🌍 بین‌المللی — رسانه",
    "بین‌المللی_تخصصی":     "🌿 بین‌المللی — تخصصی",
    "سازمان‌بین‌المللی":    "🏛️ سازمان‌های بین‌المللی",
    "منطقه‌ای_عربی_آسیایی": "🌏 عربی / آسیایی",
    "نشریه_علمی":            "🔬 نشریات علمی",
}
