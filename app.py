import math
import asyncio
import datetime
import json
import os
import logging
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events, functions, types, Button
from telethon.errors import RPCError


# ============================================================
# 🔐 الإعدادات السرية
# ============================================================
#
# ضعها في Environment Variables:
#
# API_ID
# API_HASH
# TOKEN_1
# TOKEN_2
#
# مثال:
# API_ID=123456
# API_HASH=xxxxxxxxxxxxxxxx
# TOKEN_1=xxxxxxxx
# TOKEN_2=xxxxxxxx
#
# لا تضع الأسرار داخل الكود.
# ============================================================

API_ID = 32361464
API_HASH = "efa6fd8d917173938f503ec3659122cd"

TOKEN_1 = "8141677792:AAF1ckm3Hhiz5LBwbYIohV2syBVQGzXhQeg"
TOKEN_2 = "8624653698:AAGhsTFCFwn9XWMYGjoeJYT4e41Q9cRW3RY"

if not API_ID or not API_HASH:
    raise RuntimeError(
        "❌ API_ID أو API_HASH غير موجودين في Environment Variables."
    )

if not TOKEN_1:
    raise RuntimeError(
        "❌ TOKEN_1 غير موجود في Environment Variables."
    )

if not TOKEN_2:
    raise RuntimeError(
        "❌ TOKEN_2 غير موجود في Environment Variables."
    )


# ============================================================
# 🤖 أسماء جلسات Telethon
# ============================================================

MONITOR_SESSION = "monitor_session"
BOT2_SESSION = "almorakeb_bot_session"


# ============================================================
# 👁️ حساب مراقبة البث
# ============================================================

monitor_client = TelegramClient(
    MONITOR_SESSION,
    API_ID,
    API_HASH
)

MONITOR_INTERVAL = 60
MISSING_GRACE_PERIOD = 600

MONITOR_CHANNEL = "@kamk_00"

# 🔗 رابط البث الجديد
VOICE_CHAT_URL = "https://t.me/kamk_00?livestream"


# ============================================================
# 🤖 Bot 2 - Telethon MTProto
# ============================================================

bot2 = TelegramClient(
    BOT2_SESSION,
    API_ID,
    API_HASH
)


# ============================================================
# 📁 الملفات
# ============================================================

ACTIVATED_USERS_FILE = "activated_users.json"
ADMIN_GROUP_FILE = "admin_group.json"


# ============================================================
# 📊 البيانات
# ============================================================

activated_users = set()

pending_session_entries = {}

session_students = {}

session_active = {}

registration_open = {}

session_tokens = {}

daily_user_stats = {}

registered_chats = set()

monitor_tasks = {}

session_message_ids = {}

admin_group_chat_id = None

monitor_channel_entity = None


# ============================================================
# BOT 1 - ALJADAWEL
# ============================================================

BASE_URL_1 = f"https://api.telegram.org/bot{TOKEN_1}"

users_1 = {}

SUBJECTS_1 = {
    "scientific": [
        "الإسلامية",
        "العربي",
        "الإنكليزي",
        "الرياضيات",
        "الكيمياء",
        "الفيزياء",
        "الأحياء"
    ],
    "literary": [
        "الإسلامية",
        "العربي",
        "الإنكليزي",
        "الرياضيات",
        "التاريخ",
        "الجغرافية",
        "الاقتصاد"
    ]
}

WEEK_DAYS_1 = [
    "الأحد",
    "الاثنين",
    "الثلاثاء",
    "الأربعاء",
    "الخميس",
    "الجمعة",
    "السبت"
]


# ============================================================
# BOT 1 API
# ============================================================

async def telegram_1(
    method,
    data=None
):

    import httpx

    try:

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            response = await client.post(
                f"{BASE_URL_1}/{method}",
                data=data
            )

            return response.json()

    except Exception as e:

        print(
            "Telegram 1 Error:",
            e
        )

        return None


async def send_message_1(
    chat_id,
    text,
    keyboard=None
):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:

        data["reply_markup"] = json.dumps(
            {
                "inline_keyboard": keyboard
            },
            ensure_ascii=False
        )

    return await telegram_1(
        "sendMessage",
        data
    )


def create_fixed_plan_1(
    selected,
    days
):

    weeks = math.ceil(
        days / 7
    )

    plan = [
        []
        for _ in range(7)
    ]

    load = [
        0
        for _ in range(7)
    ]

    for subject in selected:

        weekly = math.ceil(
            subject["count"] / weeks
        )

        weekly = min(
            weekly,
            subject["count"]
        )

        for _ in range(weekly):

            best_day = 0

            for d in range(1, 7):

                if load[d] < load[best_day]:
                    best_day = d

            found = None

            for item in plan[best_day]:

                if item["name"] == subject["name"]:

                    found = item

                    break

            if found:

                found["count"] += 1

            else:

                plan[best_day].append(
                    {
                        "name": subject["name"],
                        "count": 1
                    }
                )

            load[best_day] += 1

    return {
        "plan": plan,
        "weeks": weeks
    }


def format_plan_1(
    selected,
    days,
    result
):

    total = sum(
        subject["count"]
        for subject in selected
    )

    weeks = result["weeks"]

    text = (
        "📚 جدولك الأسبوعي الثابت\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 المجموع: {total} محاضرة\n"
        f"⏳ المدة: {days} يوم\n"
        f"📅 تقريبًا: {weeks} أسبوع\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for i in range(7):

        text += (
            f"📌 {WEEK_DAYS_1[i]}\n"
        )

        items = result["plan"][i]

        if not items:

            text += "راحة 😴\n"

        else:

            for item in items:

                text += (
                    f"• {item['name']} — "
                    f"{item['count']} محاضرة\n"
                )

        text += "\n"

    text += (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔄 شلون تمشي على الجدول؟\n\n"
        "هذا الجدول ثابت وليس جدولًا يتغير كل أسبوع.\n"
    )

    return text


async def ask_next_subject_1(
    chat_id
):

    user = users_1[chat_id]

    index = user["subject_index"]

    subjects = SUBJECTS_1[
        user["branch"]
    ]

    if index >= len(subjects):

        user["state"] = "waiting_days"

        await send_message_1(
            chat_id,
            "🎯 ممتاز!\n\n"
            "هسه اكتب عدد الأيام اللي تريد تخلص خلالها كل المحاضرات.\n"
            "مثلاً: 7, 14, 30, 60"
        )

        return

    subject = subjects[index]

    user["current_subject"] = subject

    user["state"] = "waiting_lectures"

    await send_message_1(
        chat_id,
        f"📘 المادة: {subject}\n\n"
        "كم عدد المحاضرات الكاملة لهذه المادة؟\n"
        "إذا ما تريدها بالخطة اكتب 0."
    )


async def start_user_1(
    chat_id
):

    users_1[chat_id] = {

        "state": "waiting_branch",

        "branch": None,

        "subjects": [],

        "subject_index": 0,

        "current_subject": None,

        "days": None,

        "result": None
    }

    await send_message_1(
        chat_id,
        "📚 أهلاً بك في مخطط أكاديمية السادس\n\n"
        "حدد الفرع حتى نبدأ بإنشاء جدولك الدراسي الأسبوعي الثابت 🔥",
        [[
            {
                "text": "🔬 السادس العلمي",
                "callback_data": "branch_scientific"
            },
            {
                "text": "📖 السادس الأدبي",
                "callback_data": "branch_literary"
            }
        ]]
    )


async def handle_message_1(
    message
):

    if "chat" not in message:
        return

    chat_id = message["chat"]["id"]

    text = message.get(
        "text",
        ""
    ).strip()

    if text == "/start":

        await start_user_1(chat_id)

        return

    if chat_id not in users_1:

        await start_user_1(chat_id)

        return

    user = users_1[chat_id]

    state = user["state"]

    if state == "waiting_lectures":

        try:

            count = int(text)

            if count < 0:
                raise ValueError

        except Exception:

            await send_message_1(
                chat_id,
                "❌ اكتب رقم صحيح فقط.\n"
                "مثلاً: 30 أو 0 إذا ما تريد المادة."
            )

            return

        subject = user["current_subject"]

        if count > 0:

            user["subjects"].append(
                {
                    "name": subject,
                    "count": count
                }
            )

        user["subject_index"] += 1

        await ask_next_subject_1(
            chat_id
        )

        return

    if state == "waiting_days":

        try:

            days = int(text)

            if days < 1:
                raise ValueError

        except Exception:

            await send_message_1(
                chat_id,
                "❌ اكتب عدد أيام صحيح.\n"
                "مثلاً: 7 أو 14 أو 30."
            )

            return

        user["days"] = days

        result = create_fixed_plan_1(
            user["subjects"],
            days
        )

        text_plan = format_plan_1(
            user["subjects"],
            days,
            result
        )

        await send_message_1(
            chat_id,
            text_plan,
            [[
                {
                    "text": "↩️ تعديل الخطة",
                    "callback_data": "reset_plan"
                }
            ]]
        )

        user["state"] = "finished"


async def handle_callback_1(
    callback
):

    callback_id = callback["id"]

    chat_id = (
        callback["message"]
        ["chat"]["id"]
    )

    data = callback["data"]

    await telegram_1(
        "answerCallbackQuery",
        {
            "callback_query_id":
                callback_id
        }
    )

    if data in [
        "branch_scientific",
        "branch_literary"
    ]:

        branch = (
            "scientific"
            if data == "branch_scientific"
            else "literary"
        )

        users_1[chat_id] = {

            "state":
                "waiting_lectures",

            "branch":
                branch,

            "subjects": [],

            "subject_index":
                0,

            "current_subject":
                None,

            "days":
                None,

            "result":
                None
        }

        await telegram_1(
            "editMessageText",
            {
                "chat_id":
                    chat_id,

                "message_id":
                    callback["message"]
                    ["message_id"],

                "text":
                    (
                        "تم اختيار الفرع بنجاح. "
                        "هسه راح نسألك عن عدد المحاضرات لكل مادة."
                    )
            }
        )

        await ask_next_subject_1(
            chat_id
        )

        return

    if data == "reset_plan":

        await start_user_1(
            chat_id
        )


async def run_bot_1():

    print(
        "🤖 البوت الأول (aljadawel) يعمل الآن..."
    )

    offset = None

    while True:

        try:

            data = {
                "timeout": 30,
                "allowed_updates":
                    '["message","callback_query"]'
            }

            if offset is not None:
                data["offset"] = offset

            response = await telegram_1(
                "getUpdates",
                data
            )

            if (
                not response
                or
                not response.get("ok")
            ):

                await asyncio.sleep(2)

                continue

            for update in response["result"]:

                offset = (
                    update["update_id"] + 1
                )

                if "message" in update:

                    await handle_message_1(
                        update["message"]
                    )

                elif "callback_query" in update:

                    await handle_callback_1(
                        update["callback_query"]
                    )

        except Exception as e:

            print(
                "Bot 1 Error:",
                e
            )

            await asyncio.sleep(5)


# ============================================================
# 💾 ACTIVATED USERS
# ============================================================

def load_activated_users():

    global activated_users

    try:

        if not os.path.exists(
            ACTIVATED_USERS_FILE
        ):

            activated_users = set()

            print(
                "🔐 لا يوجد ملف طلاب مفعّلين."
            )

            return

        with open(
            ACTIVATED_USERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):

            activated_users = {
                int(x)
                for x in data
            }

        else:

            activated_users = set()

        print(
            f"🔐 تم تحميل "
            f"{len(activated_users)} طالب مفعّل."
        )

    except Exception as e:

        activated_users = set()

        print(
            f"❌ خطأ بتحميل الطلاب المفعّلين: {e}"
        )


def save_activated_users():

    try:

        with open(
            ACTIVATED_USERS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                sorted(
                    list(activated_users)
                ),
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            f"❌ خطأ بحفظ الطلاب المفعّلين: {e}"
        )


def is_user_activated(
    user_id
):

    return user_id in activated_users


def activate_user(
    user_id
):

    if user_id not in activated_users:

        activated_users.add(
            user_id
        )

        save_activated_users()

        print(
            f"🔐 تم تفعيل المستخدم: {user_id}"
        )


# ============================================================
# ⚙️ ADMIN GROUP
# ============================================================

def load_admin_group():

    global admin_group_chat_id

    try:

        if not os.path.exists(
            ADMIN_GROUP_FILE
        ):

            admin_group_chat_id = None

            print(
                "⚙️ لم يتم تعيين گروب المشرفين بعد."
            )

            return

        with open(
            ADMIN_GROUP_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):

            value = data.get("chat_id")

            if value is not None:

                admin_group_chat_id = int(
                    value
                )

            else:

                admin_group_chat_id = None

        else:

            admin_group_chat_id = None

        if admin_group_chat_id:

            print(
                "⚙️ تم تحميل گروب المشرفين:"
                f" {admin_group_chat_id}"
            )

    except Exception as e:

        admin_group_chat_id = None

        print(
            f"❌ خطأ بتحميل گروب المشرفين: {e}"
        )


def save_admin_group(
    chat_id
):

    global admin_group_chat_id

    try:

        admin_group_chat_id = int(
            chat_id
        )

        with open(
            ADMIN_GROUP_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                {
                    "chat_id":
                        admin_group_chat_id
                },
                file,
                ensure_ascii=False,
                indent=2
            )

        print(
            "💾 تم حفظ گروب المشرفين:"
            f" {admin_group_chat_id}"
        )

        return True

    except Exception as e:

        print(
            f"❌ خطأ بحفظ گروب المشرفين: {e}"
        )

        return False


# ============================================================
# 👤 ADMIN CHECK - BOT 2
# ============================================================

async def is_admin(
    event
):

    try:

        if not event.is_group:
            return False

        sender = await event.get_sender()

        if sender is None:
            return False

        permissions = await bot2.get_permissions(
            event.chat_id,
            sender
        )

        return bool(
            getattr(
                permissions,
                "is_admin",
                False
            )
            or
            getattr(
                permissions,
                "is_creator",
                False
            )
        )

    except Exception as e:

        print(
            f"⚠️ خطأ بفحص صلاحية المشرف: {e}"
        )

        return False


async def is_admin_group(
    event
):

    if admin_group_chat_id is None:
        return False

    return (
        event.chat_id
        ==
        admin_group_chat_id
    )


async def check_bot_is_admin(
    chat_id
):

    try:

        me = await bot2.get_me()

        permissions = await bot2.get_permissions(
            chat_id,
            me
        )

        return bool(
            getattr(
                permissions,
                "is_admin",
                False
            )
            or
            getattr(
                permissions,
                "is_creator",
                False
            )
        )

    except Exception as e:

        print(
            "⚠️ تعذر التحقق من صلاحية البوت:"
            f" {e}"
        )

        return False


# ============================================================
# ⚙️ SET ADMIN GROUP
# ============================================================

async def set_admin_group(
    event
):

    if not event.is_group:

        await event.reply(
            "❌ هذا الأمر لازم تستخدمه داخل گروب المشرفين."
        )

        return

    if not await is_admin(event):

        print(
            "🚫 شخص غير مشرف حاول تعيين گروب المشرفين."
        )

        return

    bot_is_admin = await check_bot_is_admin(
        event.chat_id
    )

    if not bot_is_admin:

        await event.reply(
            "⚠️ لازم تضيفون البوت كـ أدمن بالگروب أولاً، "
            "وبعدها أرسلوا:\n\n"
            "#تعيين_گروب_المشرفين"
        )

        return

    saved = save_admin_group(
        event.chat_id
    )

    if not saved:

        await event.reply(
            "❌ صار خطأ بحفظ گروب المشرفين."
        )

        return

    await event.reply(
        "✅ تم تعيين هذا الگروب كـ گروب المشرفين بنجاح.\n\n"
        "📊 من هسه الأمر:\n"
        "`#الاحصائيات`\n"
        "يشتغل بهذا الگروب فقط.\n\n"
        "💾 وتم حفظ الإعداد."
    )


# ============================================================
# 🔍 FIND MONITOR CHANNEL
# ============================================================

async def find_monitor_channel():

    global monitor_channel_entity

    if monitor_channel_entity is not None:
        return monitor_channel_entity

    print(
        "🔍 محاولة الوصول إلى قناة البث..."
    )

    try:

        entity = await monitor_client.get_entity(
            MONITOR_CHANNEL
        )

        monitor_channel_entity = entity

        print(
            "✅ تم العثور على قناة البث."
        )

        print(
            f"   🆔 Channel ID: "
            f"{getattr(entity, 'id', 'غير معروف')}"
        )

        print(
            f"   📛 Title: "
            f"{getattr(entity, 'title', 'غير معروف')}"
        )

        return entity

    except Exception as e:

        print(
            "⚠️ تعذر حل username مباشرة:"
        )

        print(
            f"   {type(e).__name__}: {e}"
        )

    try:

        target_username = (
            MONITOR_CHANNEL
            .replace("@", "")
            .lower()
        )

        async for dialog in monitor_client.iter_dialogs():

            entity = dialog.entity

            username = getattr(
                entity,
                "username",
                None
            )

            title = getattr(
                entity,
                "title",
                None
            )

            if (
                username
                and
                str(username).lower()
                ==
                target_username
            ):

                monitor_channel_entity = entity

                return entity

            if (
                title
                and
                target_username
                in
                str(title).lower()
            ):

                monitor_channel_entity = entity

                return entity

    except Exception as e:

        print(
            f"❌ خطأ أثناء البحث داخل Dialogs: {e}"
        )

    return None


# ============================================================
# 📡 GET ACTIVE VOICE CHAT
# ============================================================

async def get_active_group_call():

    channel = await find_monitor_channel()

    if channel is None:

        print(
            "❌ لا يمكن الوصول إلى قناة البث."
        )

        return None

    try:

        full = await monitor_client(
            functions.channels.GetFullChannelRequest(
                channel=channel
            )
        )

        call = full.full_chat.call

        if not call:

            print(
                "ℹ️ لا يوجد Voice Chat نشط حالياً."
            )

            return None

        print(
            "📡 تم اكتشاف Voice Chat تلقائياً."
        )

        return call

    except Exception as e:

        print(
            "❌ خطأ أثناء اكتشاف Voice Chat:"
        )

        print(
            f"   {type(e).__name__}: {e}"
        )

        return None


# ============================================================
# 👥 GET LIVE PARTICIPANTS
# ============================================================

async def get_live_participant_ids():

    try:

        call = await get_active_group_call()

        if call is None:
            return set()

        try:

            result = await monitor_client(
                functions.phone.GetGroupCallRequest(
                    call=call,
                    limit=100,
                    offset=0
                )
            )

        except TypeError:

            input_call = types.InputGroupCall(
                id=call.id,
                access_hash=call.access_hash
            )

            result = await monitor_client(
                functions.phone.GetGroupCallRequest(
                    call=input_call,
                    limit=100,
                    offset=0
                )
            )

        except Exception as e:

            print(
                "❌ فشل جلب المشاركين:"
            )

            print(
                f"   {type(e).__name__}: {e}"
            )

            return None

        participant_ids = set()

        participants = getattr(
            result,
            "participants",
            []
        )

        print(
            f"👥 Telegram رجّع "
            f"{len(participants)} مشارك."
        )

        for participant in participants:

            peer = getattr(
                participant,
                "peer",
                None
            )

            if peer is None:
                continue

            user_id = getattr(
                peer,
                "user_id",
                None
            )

            if user_id is not None:

                participant_ids.add(
                    int(user_id)
                )

        print(
            f"👥 الموجودين حالياً: "
            f"{len(participant_ids)}"
        )

        return participant_ids

    except Exception as e:

        print(
            "❌ خطأ أثناء الوصول إلى البث:"
        )

        print(
            f"   {type(e).__name__}: {e}"
        )

        return None


# ============================================================
# 📩 PRIVATE WARNING
# ============================================================

async def send_missing_private_message(
    user_id,
    user_name
):

    try:

        message = await bot2.send_message(
            user_id,
            (
                f"⚠️ عزيزي {user_name}، "
                "ما لكيناك حالياً داخل البث.\n\n"
                "⏳ عندك 10 دقائق ترجع للبث، "
                "وإذا ما رجعت خلال المهلة يتم إقصاؤك "
                "تلقائياً من قائمة المسجلين بالسشن.\n\n"
                "🔗 رابط البث:\n"
                f"{VOICE_CHAT_URL}\n\n"
                "©️ @kamk_00"
            )
        )

        print(
            f"✅ تم إرسال الإنذار إلى {user_name}"
        )

        return True

    except Exception as e:

        print(
            f"❌ فشل إرسال الإنذار إلى "
            f"{user_name}: {e}"
        )

        return False


# ============================================================
# 👁️ PRESENCE MONITOR
# ============================================================

async def monitor_session_presence(
    chat_id
):

    print(
        f"👁️ بدأت مراقبة البث للسشن "
        f"{chat_id}"
    )

    try:

        while session_active.get(chat_id):

            print(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

            participant_ids = (
                await get_live_participant_ids()
            )

            if participant_ids is None:

                await asyncio.sleep(
                    MONITOR_INTERVAL
                )

                continue

            students = session_students.get(
                chat_id,
                {}
            )

            now = datetime.datetime.now(
                datetime.timezone.utc
            )

            for user_id, info in list(
                students.items()
            ):

                student_name = info["name"]

                if user_id in participant_ids:

                    info["missing_since"] = None
                    info["warning_sent"] = False

                    print(
                        f"✅ {student_name} موجود."
                    )

                    continue

                print(
                    f"❌ {student_name} غير موجود."
                )

                if not info.get(
                    "missing_since"
                ):

                    info["missing_since"] = now
                    info["warning_sent"] = True

                    await send_missing_private_message(
                        user_id,
                        student_name
                    )

                    continue

                missing_seconds = (
                    now
                    -
                    info["missing_since"]
                ).total_seconds()

                remaining = max(
                    0,
                    int(
                        MISSING_GRACE_PERIOD
                        -
                        missing_seconds
                    )
                )

                print(
                    f"⏳ {student_name}: "
                    f"{remaining} ثانية"
                )

                if (
                    missing_seconds
                    >=
                    MISSING_GRACE_PERIOD
                ):

                    final_ids = (
                        await get_live_participant_ids()
                    )

                    if final_ids is None:
                        continue

                    if user_id in final_ids:

                        info["missing_since"] = None
                        info["warning_sent"] = False

                        continue

                    if (
                        user_id
                        in
                        session_students.get(
                            chat_id,
                            {}
                        )
                    ):

                        del session_students[
                            chat_id
                        ][user_id]

                        try:

                            await bot2.send_message(
                                chat_id,
                                (
                                    f"🚨 تم إقصاء الطالب "
                                    f"{student_name} "
                                    "لأنه لم يرجع للبث "
                                    "خلال 10 دقائق.\n\n"
                                    "©️ @kamk_00"
                                )
                            )

                        except Exception as e:

                            print(
                                f"⚠️ تعذر إرسال رسالة الإقصاء: {e}"
                            )

            await asyncio.sleep(
                MONITOR_INTERVAL
            )

    except asyncio.CancelledError:

        print(
            f"🛑 توقفت مراقبة السشن {chat_id}"
        )

    except Exception as e:

        print(
            f"❌ خطأ في مراقبة السشن {chat_id}: "
            f"{type(e).__name__}: {e}"
        )


def start_presence_monitor(
    chat_id
):

    old_task = monitor_tasks.get(
        chat_id
    )

    if (
        old_task
        and
        not old_task.done()
    ):

        old_task.cancel()

    monitor_tasks[chat_id] = (
        asyncio.create_task(
            monitor_session_presence(
                chat_id
            )
        )
    )


# ============================================================
# 🚀 START SESSION
# ============================================================

async def start_session(
    chat_id
):

    registered_chats.add(
        chat_id
    )

    if session_active.get(chat_id):

        await bot2.send_message(
            chat_id,
            "⚠️ توجد سشن مفتوحة أو قيد التحضير حالياً!"
        )

        return

    session_active[chat_id] = True

    session_tokens[chat_id] = (
        session_tokens.get(
            chat_id,
            0
        )
        + 1
    )

    current_token = session_tokens[chat_id]

    await bot2.send_message(
        chat_id,
        (
            "🔔 **تنبيه السشن**\n\n"
            "السشن راح يبدأ بعد **دقيقتين** إن شاء الله.\n\n"
            "جهزوا نفسكم، وبعد بداية السشن "
            "راح تظهر أزرار تسجيل الحضور.\n\n"
            "📌 التسجيل يبقى مفتوح لمدة **20 دقيقة**.\n\n"
            "©️ @kamk_00"
        )
    )

    await asyncio.sleep(
        120
    )

    if (
        not session_active.get(chat_id)
        or
        session_tokens.get(chat_id)
        != current_token
    ):

        return

    session_students[chat_id] = {}

    registration_open[chat_id] = True

    buttons = [
        [
            Button.inline(
                "🙋‍♂️ أني ادخل السشن",
                b"entered_session"
            )
        ],
        [
            Button.inline(
                "❌ أني مادخل السشن",
                b"not_entered"
            )
        ]
    ]

    sent_message = await bot2.send_message(
        chat_id,
        (
            "🎯 **بدأت سشن الحضور الآن!**\n\n"
            "أمامك 20 دقيقة للتسجيل.\n\n"
            "©️ @kamk_00"
        ),
        buttons=buttons
    )

    session_message_ids[
        chat_id
    ] = sent_message.id

    async def delayed_close():

        await asyncio.sleep(
            1200
        )

        if (
            not session_active.get(chat_id)
            or
            session_tokens.get(chat_id)
            != current_token
        ):

            return

        registration_open[chat_id] = False

        message_id = session_message_ids.get(
            chat_id
        )

        if message_id:

            try:

                await bot2.edit_message(
                    chat_id,
                    message_id,
                    buttons=None
                )

            except Exception as e:

                print(
                    f"⚠️ تعذر إزالة أزرار التسجيل: {e}"
                )

        try:

            await bot2.send_message(
                chat_id,
                (
                    "⏳ **انتهى التسجيل للسشن!**\n\n"
                    "👁️ بدأت مراقبة الحضور الآن.\n\n"
                    "©️ @kamk_00"
                )
            )

        except Exception as e:

            print(
                f"⚠️ تعذر إرسال انتهاء التسجيل: {e}"
            )

        start_presence_monitor(
            chat_id
        )

    asyncio.create_task(
        delayed_close()
    )


# ============================================================
# 🛑 END SESSION
# ============================================================

async def end_session(
    chat_id
):

    registered_chats.add(
        chat_id
    )

    if not session_active.get(chat_id):

        await bot2.send_message(
            chat_id,
            "⚠️ لا توجد سشن مفتوحة حالياً!"
        )

        return

    session_active[chat_id] = False

    registration_open[chat_id] = False

    session_tokens[chat_id] = (
        session_tokens.get(
            chat_id,
            0
        )
        + 1
    )

    message_id = session_message_ids.get(
        chat_id
    )

    if message_id:

        try:

            await bot2.edit_message(
                chat_id,
                message_id,
                buttons=None
            )

        except Exception:
            pass

    monitor_task = monitor_tasks.get(
        chat_id
    )

    if (
        monitor_task
        and
        not monitor_task.done()
    ):

        monitor_task.cancel()

    students = session_students.get(
        chat_id,
        {}
    )

    list_text = (
        f"📋 **قائمة الطلاب الأبطال "
        f"({len(students)} طالب):**\n\n"
    )

    for idx, (
        uid,
        info
    ) in enumerate(
        students.items(),
        1
    ):

        list_text += (
            f"{idx}. {info['name']}\n"
        )

        daily_user_stats.setdefault(
            uid,
            {
                "name": info["name"],
                "completed_sessions": 0
            }
        )

        daily_user_stats[
            uid
        ]["completed_sessions"] += 1

    await bot2.send_message(
        chat_id,
        list_text + "\n©️ @kamk_00"
    )

    session_students[chat_id] = {}


# ============================================================
# 📊 DAILY STATISTICS
# ============================================================

async def send_daily_statistics(
    event
):

    if not await is_admin(event):
        return

    if not await is_admin_group(event):
        return

    today = datetime.datetime.now(
        ZoneInfo("Asia/Baghdad")
    )

    date_text = today.strftime(
        "%d/%m/%Y"
    )

    if not daily_user_stats:

        await event.reply(
            (
                "📊 **إحصائيات اليوم**\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "❌ ماكو أي سشنات مكتملة اليوم لحد الآن.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"📅 {date_text}"
            )
        )

        return

    sorted_students = sorted(
        daily_user_stats.values(),
        key=lambda x:
            x["completed_sessions"],
        reverse=True
    )

    total_completed_sessions = sum(
        student["completed_sessions"]
        for student in sorted_students
    )

    text = (
        "📊 **إحصائيات اليوم**\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 عدد الطلاب: {len(sorted_students)}\n"
        f"🎯 مجموع السشنات المكتملة: "
        f"{total_completed_sessions}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for idx, student in enumerate(
        sorted_students,
        1
    ):

        text += (
            f"{idx}. {student['name']} — "
            f"{student['completed_sessions']} سشنات\n"
        )

    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        f"📅 {date_text}"
    )

    await event.reply(
        text
    )


# ============================================================
# 🕛 DAILY RESET
# ============================================================

async def schedule_daily_reset():

    iraq_tz = ZoneInfo(
        "Asia/Baghdad"
    )

    print(
        "🕛 نظام تصفير اليوم بدأ العمل."
    )

    while True:

        try:

            now = datetime.datetime.now(
                iraq_tz
            )

            target = (
                now.replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                +
                datetime.timedelta(days=1)
            )

            wait_seconds = (
                target - now
            ).total_seconds()

            print(
                "🕛 التصفير القادم الساعة 00:00 "
                "بتوقيت بغداد، بعد "
                f"{int(wait_seconds)} ثانية."
            )

            await asyncio.sleep(
                wait_seconds
            )

            daily_user_stats.clear()

            for chat_id in list(
                session_students.keys()
            ):

                session_students[chat_id] = {}

            pending_session_entries.clear()

            print(
                "🌅 بدأ يوم جديد من الصفر."
            )

        except asyncio.CancelledError:

            print(
                "🛑 تم إيقاف نظام التصفير."
            )

            break

        except Exception as e:

            print(
                f"❌ خطأ في نظام التصفير: {e}"
            )

            await asyncio.sleep(
                60
            )


# ============================================================
# 🔗 CREATE ACTIVATION URL
# ============================================================

async def create_session_activation_url(
    chat_id
):

    try:

        bot_info = await bot2.get_me()

        bot_username = getattr(
            bot_info,
            "username",
            None
        )

        if not bot_username:
            return None

        token = session_tokens.get(
            chat_id
        )

        if token is None:
            return None

        payload = (
            f"session_{chat_id}_{token}"
        )

        return (
            f"https://t.me/"
            f"{bot_username}"
            f"?start={payload}"
        )

    except Exception as e:

        print(
            f"❌ تعذر إنشاء رابط التفعيل: {e}"
        )

        return None


# ============================================================
# 🙋 ENTER SESSION
# ============================================================

async def handle_entered_session(
    event
):

    user = await event.get_sender()

    if user is None:
        return

    chat_id = event.chat_id

    user_id = user.id

    user_full_name = (
        f"{user.first_name or ''} "
        f"{user.last_name or ''}"
    ).strip()

    if is_user_activated(user_id):

        session_students.setdefault(
            chat_id,
            {}
        )[user_id] = {

            "name":
                user_full_name,

            "missing_since":
                None,

            "warning_sent":
                False
        }

        await event.answer(
            "✅ تم تسجيل حضورك!"
        )

        print(
            f"🙋‍♂️ {user_full_name} "
            f"تسجل مباشرة."
        )

        return

    activation_url = (
        await create_session_activation_url(
            chat_id
        )
    )

    if not activation_url:

        await event.answer(
            "⚠️ تعذر فتح التفعيل، حاول مرة ثانية.",
            alert=True
        )

        return

    pending_session_entries[
        user_id
    ] = {

        "chat_id":
            chat_id,

        "token":
            session_tokens.get(
                chat_id
            )
    }

    await event.answer(
        "🔐 لازم تفعّل بوت المراقب أولاً.",
        url=activation_url
    )

    print(
        f"🔗 {user_full_name} "
        "غير مفعّل وتم توجيهه للتفعيل."
    )


# ============================================================
# 🔘 BUTTON HANDLER
# ============================================================

@bot2.on(
    events.CallbackQuery
)
async def bot2_callback_handler(
    event
):

    try:

        data = event.data.decode(
            "utf-8"
        )

        chat_id = event.chat_id

        if not session_active.get(chat_id):

            await event.answer(
                "⚠️ هذه السشن انتهت أو توقفت!",
                alert=True
            )

            return

        if data == "entered_session":

            if not registration_open.get(
                chat_id
            ):

                await event.answer(
                    "❌ عذراً، انتهى التسجيل!",
                    alert=True
                )

                return

            await handle_entered_session(
                event
            )

            return

        if data == "not_entered":

            sender = await event.get_sender()

            if (
                sender
                and
                chat_id in session_students
                and
                sender.id in session_students[
                    chat_id
                ]
            ):

                del session_students[
                    chat_id
                ][sender.id]

            await event.answer(
                "📌 تم تسجيل اختيارك!"
            )

            return

    except Exception as e:

        print(
            f"❌ خطأ Callback: "
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# 🟢 /START
# ============================================================

@bot2.on(
    events.NewMessage(
        pattern=r"^/start(?:\s+(.+))?$"
    )
)
async def bot2_start_handler(
    event
):

    try:

        user = await event.get_sender()

        if user is None:
            return

        user_id = user.id

        was_activated = (
            is_user_activated(user_id)
        )

        activate_user(
            user_id
        )

        payload = ""

        if event.pattern_match.group(1):

            payload = (
                event.pattern_match.group(1)
                .strip()
            )

        if payload.startswith(
            "session_"
        ):

            try:

                parts = payload.split("_")

                if len(parts) != 3:
                    raise ValueError

                target_chat_id = int(
                    parts[1]
                )

                target_token = int(
                    parts[2]
                )

            except Exception:

                await event.reply(
                    "✅ تم تفعيل بوت المراقب بنجاح."
                )

                return

            if (
                session_active.get(
                    target_chat_id
                )
                and
                registration_open.get(
                    target_chat_id
                )
                and
                session_tokens.get(
                    target_chat_id
                )
                ==
                target_token
            ):

                user_full_name = (
                    f"{user.first_name or ''} "
                    f"{user.last_name or ''}"
                ).strip()

                session_students.setdefault(
                    target_chat_id,
                    {}
                )[user_id] = {

                    "name":
                        user_full_name,

                    "missing_since":
                        None,

                    "warning_sent":
                        False
                }

                await event.reply(
                    "✅ تم تفعيل بوت المراقب!\n\n"
                    "🙋‍♂️ وتم تسجيلك تلقائياً "
                    "بالسشن اللي كنت ضاغط عليها."
                )

                return

            await event.reply(
                "✅ تم تفعيل بوت المراقب بنجاح.\n\n"
                "⚠️ لكن التسجيل بهذه السشن انتهى بالفعل."
            )

            return

        if was_activated:

            await event.reply(
                "✅ بوت المراقب مفعّل عندك مسبقاً.\n\n"
                "ما تحتاج تسوي أي شيء إضافي."
            )

        else:

            await event.reply(
                "✅ تم تفعيل بوت مراقب الأكاديمية بنجاح!\n\n"
                "هسه أگدر أراسلك بالخاص عند الحاجة "
                "وأرسل لك تنبيهات السشن."
            )

    except Exception as e:

        print(
            f"❌ خطأ /start: {e}"
        )


# ============================================================
# 🟢 /SESSION
# ============================================================

@bot2.on(
    events.NewMessage(
        pattern=r"^/session$"
    )
)
async def bot2_session_handler(
    event
):

    try:

        if not await is_admin(event):
            return

        await start_session(
            event.chat_id
        )

    except Exception as e:

        print(
            f"❌ خطأ /session: {e}"
        )


# ============================================================
# 🔴 /END
# ============================================================

@bot2.on(
    events.NewMessage(
        pattern=r"^/end$"
    )
)
async def bot2_end_handler(
    event
):

    try:

        if not await is_admin(event):
            return

        await end_session(
            event.chat_id
        )

    except Exception as e:

        print(
            f"❌ خطأ /end: {e}"
        )


# ============================================================
# 📝 HASH COMMANDS
# ============================================================

@bot2.on(
    events.NewMessage(
        incoming=True
    )
)
async def bot2_text_handler(
    event
):

    try:

        text = (
            event.raw_text
            or
            ""
        ).strip()

        if not text:
            return

        # تجاهل أوامر /start و /session و /end
        if text.startswith("/start"):
            return

        if text == "/session":
            return

        if text == "/end":
            return

        # ----------------------------------------
        # تعيين مجموعة المشرفين
        # ----------------------------------------

        if (
            "#تعيين_گروب_المشرفين"
            in text
            or
            "#تعيين_مجموعة_المشرفين"
            in text
        ):

            await set_admin_group(
                event
            )

            return

        # ----------------------------------------
        # الإحصائيات
        # ----------------------------------------

        if "#الاحصائيات" in text:

            if not await is_admin_group(event):
                return

            await send_daily_statistics(
                event
            )

            return

        # ----------------------------------------
        # بدء السشن
        # ----------------------------------------

        if "#بدء_السشن" in text:

            if not await is_admin(event):
                return

            registered_chats.add(
                event.chat_id
            )

            print(
                f"🎯 تم استلام أمر بدء السشن "
                f"من {event.chat_id}"
            )

            await start_session(
                event.chat_id
            )

            return

        # ----------------------------------------
        # انتهاء السشن
        # ----------------------------------------

        if "#انتهاء_السشن" in text:

            if not await is_admin(event):
                return

            registered_chats.add(
                event.chat_id
            )

            print(
                f"🏁 تم استلام أمر انتهاء السشن "
                f"من {event.chat_id}"
            )

            await end_session(
                event.chat_id
            )

            return

    except Exception as e:

        print(
            f"❌ خطأ في معالجة الرسالة: "
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# 🤖 تشغيل Bot 2 عبر MTProto
# ============================================================

async def start_bot2():

    while True:

        try:

            print(
                "========================================"
            )

            print(
                "🤖 بدء تشغيل البوت الثاني "
                "(almorakeb)"
            )

            print(
                "🔌 اتصال Bot 2 عبر Telethon MTProto..."
            )

            # ------------------------------------------------
            # تسجيل الدخول بواسطة Bot Token
            # ------------------------------------------------

            await bot2.start(
                bot_token=TOKEN_2
            )

            me = await bot2.get_me()

            print(
                "========================================"
            )

            print(
                "✅ البوت الثاني متصل بنجاح!"
            )

            print(
                f"🤖 Username: "
                f"@{me.username or 'بدون username'}"
            )

            print(
                f"🆔 ID: {me.id}"
            )

            print(
                "📡 نظام الاتصال: Telethon MTProto"
            )

            print(
                "🟢 البوت الثاني جاهز لاستقبال الرسائل."
            )

            print(
                "========================================"
            )

            # ------------------------------------------------
            # إبقاء الاتصال
            # ------------------------------------------------

            await bot2.run_until_disconnected()

            print(
                "⚠️ اتصال Bot 2 انقطع."
            )

        except asyncio.CancelledError:

            print(
                "🛑 تم إلغاء Bot 2."
            )

            raise

        except Exception as e:

            print(
                "========================================"
            )

            print(
                "⚠️ حدث خطأ في Bot 2"
            )

            print(
                f"النوع: {type(e).__name__}"
            )

            print(
                f"الخطأ: {e}"
            )

            print(
                "🔄 سيتم إعادة الاتصال بعد 10 ثوانٍ..."
            )

            print(
                "========================================"
            )

            try:

                await bot2.disconnect()

            except Exception:
                pass

            await asyncio.sleep(
                10
            )


# ============================================================
# 👁️ تشغيل حساب المراقبة
# ============================================================

async def start_monitor():

    print(
        "👁️ جاري تشغيل حساب مراقبة البث..."
    )

    await monitor_client.start()

    print(
        "✅ حساب مراقبة البث متصل بنجاح."
    )

    try:

        me = await monitor_client.get_me()

        print(
            "👤 حساب المراقبة:"
        )

        print(
            f"   ID: {me.id}"
        )

        print(
            f"   الاسم: "
            f"{me.first_name or ''} "
            f"{me.last_name or ''}".strip()
        )

        print(
            "✅ حساب المراقبة جاهز."
        )

    except Exception as e:

        print(
            "⚠️ تعذر قراءة معلومات حساب المراقبة:"
        )

        print(
            f"   {type(e).__name__}: {e}"
        )


# ============================================================
# 🚀 MAIN
# ============================================================

async def main():

    print(
        "========================================"
    )

    print(
        "🚀 جاري تشغيل كلا البوتين "
        "معاً بالتوازي بالسيرفر..."
    )

    print(
        "========================================"
    )

    load_activated_users()

    load_admin_group()

    # --------------------------------------------------------
    # حساب المراقبة
    # --------------------------------------------------------

    await start_monitor()

    # --------------------------------------------------------
    # Bot 1 + Bot 2 + Daily Reset
    # --------------------------------------------------------

    print(
        "🚀 سيتم الآن تشغيل البوتين..."
    )

    await asyncio.gather(

        run_bot_1(),

        start_bot2(),

        schedule_daily_reset()
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\n🛑 تم إيقاف السيرفر "
            "والبوتات بأمان."
        )

    except Exception as e:

        print(
            "\n❌ خطأ رئيسي:"
        )

        print(
            f"{type(e).__name__}: {e}"
        )