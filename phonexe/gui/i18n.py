"""
Bilingual (Arabic / English) string table and language state for the GUI.

Arabic is laid out right-to-left; the main window flips layout direction when
the language changes.
"""

from __future__ import annotations

_STRINGS: dict[str, dict[str, str]] = {
    # ---- app chrome ----
    "app_title": {"ar": "الأدلة والمعلومات الجنائية", "en": "Forensic Evidence & Intelligence"},
    "app_subtitle": {"ar": "فحص الأجهزة الإلكترونية", "en": "Electronic Device Examination"},
    "investigator": {"ar": "المحقق", "en": "Investigator"},
    "sys_admin": {"ar": "مسؤول النظام", "en": "System Admin"},
    # ---- top navigation ----
    "nav_dashboard": {"ar": "لوحة التحكم", "en": "Dashboard"},
    "nav_extract": {"ar": "استخراج البيانات", "en": "Data Extraction"},
    "nav_analyze": {"ar": "تحليل الأدلة", "en": "Evidence Analysis"},
    "nav_reports": {"ar": "التقارير", "en": "Reports"},
    "nav_tools": {"ar": "الأدوات", "en": "Tools"},
    # ---- device panel ----
    "connected_device": {"ar": "الجهاز المتصل", "en": "Connected Device"},
    "no_device": {"ar": "لا يوجد جهاز", "en": "No device loaded"},
    "device_info": {"ar": "معلومات الجهاز", "en": "Device Info"},
    "connected": {"ar": "تم الاتصال", "en": "Connected"},
    "main_sections": {"ar": "الأقسام الرئيسية", "en": "Main Sections"},
    "end_exam": {"ar": "إنهاء الفحص", "en": "End Examination"},
    # ---- sections ----
    "sec_overview": {"ar": "نظرة عامة", "en": "Overview"},
    "sec_apps": {"ar": "التطبيقات المثبتة", "en": "Installed Apps"},
    "sec_messages": {"ar": "الرسائل والمحادثات", "en": "Messages & Chats"},
    "sec_media": {"ar": "وسائط متعددة", "en": "Multimedia"},
    "sec_location": {"ar": "الموقع الجغرافي", "en": "Geolocation"},
    "sec_calls": {"ar": "سجل المكالمات", "en": "Call Log"},
    "sec_contacts": {"ar": "جهات الاتصال", "en": "Contacts"},
    "sec_browser": {"ar": "سجل التصفح", "en": "Browsing History"},
    "sec_accounts": {"ar": "الحسابات", "en": "Accounts"},
    "sec_deleted": {"ar": "البيانات المحذوفة", "en": "Deleted Data"},
    "sec_timeline": {"ar": "الخط الزمني", "en": "Timeline"},
    "sec_files": {"ar": "الملفات", "en": "Files"},
    "sec_calendar": {"ar": "التقويم", "en": "Calendar"},
    "sec_notes": {"ar": "الملاحظات", "en": "Notes"},
    "sec_bookmarks": {"ar": "الإشارات المرجعية", "en": "Bookmarks"},
    "sec_links": {"ar": "شبكة العلاقات", "en": "Relationships"},
    "sec_identities": {"ar": "الهويات الموحّدة", "en": "Unified Contacts"},
    "sec_audit": {"ar": "سجل التدقيق", "en": "Audit Log"},
    "save_case": {"ar": "حفظ القضية", "en": "Save Case"},
    "stories": {"ar": "الحالات", "en": "Stories"},
    "global_search": {"ar": "بحث شامل في كل البيانات...",
                      "en": "Search all data..."},
    "search_results": {"ar": "نتائج البحث", "en": "Search Results"},
    "bookmark_hint": {"ar": "نقرة مزدوجة على أي صف لإضافته للإشارات المرجعية.",
                      "en": "Double-click any row to bookmark it."},
    "reports_title": {"ar": "تصدير التقارير", "en": "Export Reports"},
    "tools_title": {"ar": "الأدوات والإعدادات", "en": "Tools & Settings"},
    "extract_title": {"ar": "استخراج البيانات", "en": "Data Extraction"},
    "export_pdf": {"ar": "تصدير PDF", "en": "Export PDF"},
    "export_html": {"ar": "تصدير HTML", "en": "Export HTML"},
    "export_json": {"ar": "تصدير JSON", "en": "Export JSON"},
    # ---- stats ----
    "stats_title": {"ar": "نظرة عامة على البيانات المستخرجة", "en": "Extracted Data Overview"},
    "refresh": {"ar": "تحديث البيانات", "en": "Refresh"},
    "stat_apps": {"ar": "التطبيقات", "en": "Apps"},
    "stat_messages": {"ar": "الرسائل", "en": "Messages"},
    "stat_photos": {"ar": "الصور", "en": "Photos"},
    "stat_calls": {"ar": "المكالمات", "en": "Calls"},
    "stat_contacts": {"ar": "جهات الاتصال", "en": "Contacts"},
    "stat_videos": {"ar": "الفيديوهات", "en": "Videos"},
    "stat_files": {"ar": "ملفات", "en": "Files"},
    "stat_deleted": {"ar": "المحذوفات", "en": "Deleted"},
    # ---- device info fields ----
    "f_name": {"ar": "اسم الجهاز", "en": "Device Name"},
    "f_os": {"ar": "نظام التشغيل", "en": "Operating System"},
    "f_model": {"ar": "الطراز", "en": "Model"},
    "f_serial": {"ar": "الرقم التسلسلي", "en": "Serial"},
    "f_imei": {"ar": "IMEI", "en": "IMEI"},
    "f_phone": {"ar": "رقم الهاتف", "en": "Phone Number"},
    "f_encryption": {"ar": "حالة التشفير", "en": "Encryption"},
    "f_enc_off": {"ar": "غير مفعّل", "en": "Disabled"},
    "extraction_status": {"ar": "حالة الاستخراج", "en": "Extraction Status"},
    "completed": {"ar": "اكتمل الاستخراج", "en": "Extraction complete"},
    "recent_events": {"ar": "آخر الأحداث", "en": "Recent Events"},
    # ---- actions / misc ----
    "open_ios": {"ar": "فتح نسخة iOS", "en": "Open iOS Backup"},
    "open_android": {"ar": "فتح استخراج Android", "en": "Open Android Extraction"},
    "open_report": {"ar": "فتح تقرير", "en": "Open Report"},
    "export_report": {"ar": "تصدير التقرير", "en": "Export Report"},
    "language": {"ar": "English", "en": "العربية"},
    "search": {"ar": "بحث...", "en": "Search..."},
    "no_data": {"ar": "لا توجد بيانات. افتح نسخة أو استخراج للبدء.",
                "en": "No data. Open a backup or extraction to begin."},
    "records": {"ar": "سجل", "en": "records"},
    "loading": {"ar": "جارٍ التحليل...", "en": "Analyzing..."},
    "scope_note": {
        "ar": "للاستخدام المصرّح به فقط — يحلل بيانات محلية من نسخة/استخراج قانوني، بدون كسر أقفال أو تشفير.",
        "en": "Authorized use only — analyzes local data from a lawful backup/extraction; no lock or encryption bypass.",
    },
    "accounts_note": {
        "ar": "يعرض معرّفات الحسابات المخزّنة محليًا فقط. لا يتم استخراج أو كسر كلمات المرور.",
        "en": "Shows locally stored account identifiers only. Passwords are not recovered or cracked.",
    },
    "deleted_note": {
        "ar": "استرجاع السجلات المحذوفة (best-effort) من المساحات الحرة لقواعد SQLite.",
        "en": "Best-effort recovery of deleted records from SQLite free space.",
    },
}


class Lang:
    """Mutable holder for the current UI language."""

    current = "ar"

    @classmethod
    def is_rtl(cls) -> bool:
        return cls.current == "ar"

    @classmethod
    def toggle(cls) -> None:
        cls.current = "en" if cls.current == "ar" else "ar"


def tr(key: str) -> str:
    entry = _STRINGS.get(key)
    if not entry:
        return key
    return entry.get(Lang.current, entry.get("en", key))
