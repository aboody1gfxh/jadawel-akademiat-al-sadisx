import requests
import time
import math

# =========================================================
# ضع توكن البوت هنا بين علامتي التنصيص
# =========================================================
TOKEN = "8877046448:AAGXOaT0C0mJPFJ6_0sp8uXSyFEYz5Tz9U8"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


# =========================================================
# بيانات المستخدمين
# =========================================================

users = {}


# =========================================================
# المواد
# =========================================================

SUBJECTS = {
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


WEEK_DAYS = [
    "الأحد",
    "الاثنين",
    "الثلاثاء",
    "الأربعاء",
    "الخميس",
    "الجمعة",
    "السبت"
]


# =========================================================
# Telegram API
# =========================================================

def telegram(method, data=None):

    try:

        response = requests.post(
            f"{BASE_URL}/{method}",
            data=data,
            timeout=60
        )

        return response.json()

    except Exception as e:

        print("Telegram Error:", e)

        return None


# =========================================================
# إرسال رسالة
# =========================================================

def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:

        data["reply_markup"] = str({
            "inline_keyboard": keyboard
        }).replace("'", '"')

    return telegram("sendMessage", data)


# =========================================================
# حذف لوحة الأزرار
# =========================================================

def remove_keyboard(chat_id, text):

    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": '{"remove_keyboard":true}'
    }

    return telegram("sendMessage", data)


# =========================================================
# اختيار الفرع
# =========================================================

def branch_keyboard():

    return [[

        {
            "text": "🔬 السادس العلمي",
            "callback_data": "branch_scientific"
        },

        {
            "text": "📖 السادس الأدبي",
            "callback_data": "branch_literary"
        }

    ]]


# =========================================================
# حساب الخطة
# =========================================================

def create_fixed_plan(selected, days):

    weeks = math.ceil(days / 7)

    plan = [[] for _ in range(7)]

    load = [0 for _ in range(7)]

    for subject in selected:

        weekly = math.ceil(subject["count"] / weeks)

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

                plan[best_day].append({

                    "name": subject["name"],
                    "count": 1

                })

            load[best_day] += 1

    return {
        "plan": plan,
        "weeks": weeks
    }


# =========================================================
# إنشاء نص الجدول
# =========================================================

def format_plan(selected, days, result):

    total = sum(
        subject["count"]
        for subject in selected
    )

    weeks = result["weeks"]

    text = ""

    text += "📚 جدولك الأسبوعي الثابت\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"

    text += f"🎯 المجموع: {total} محاضرة\n"
    text += f"⏳ المدة: {days} يوم\n"
    text += f"📅 تقريبًا: {weeks} أسبوع\n\n"

    text += "━━━━━━━━━━━━━━━━━━\n\n"

    for i in range(7):

        text += f"📌 {WEEK_DAYS[i]}\n"

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

    text += "━━━━━━━━━━━━━━━━━━\n\n"

    text += "🔄 شلون تمشي على الجدول؟\n\n"

    text += (
        "هذا الجدول ثابت وليس جدولًا يتغير كل أسبوع.\n"
        "يعني إذا كان يوم الأحد بيه 3 رياضيات، "
        "يبقى الأحد 3 رياضيات كل أسبوع.\n\n"
    )

    text += (
        f"⏳ مدة خطتك {days} يوم "
        f"— تقريبًا {weeks} أسبوع."
    )

    return text


# =========================================================
# بدء اختيار المواد
# =========================================================

def ask_subject(user_id):

    user = users[user_id]

    branch = user["branch"]

    subjects = SUBJECTS[branch]

    user["subject_index"] = 0

    ask_next_subject(user_id)


# =========================================================
# السؤال عن المادة التالية
# =========================================================

def ask_next_subject(user_id):

    user = users[user_id]

    index = user["subject_index"]

    subjects = SUBJECTS[user["branch"]]

    if index >= len(subjects):

        ask_days(user_id)

        return

    subject = subjects[index]

    user["current_subject"] = subject
    user["state"] = "waiting_lectures"

    send_message(

        user_id,

        f"📘 المادة: {subject}\n\n"
        "كم عدد المحاضرات الكاملة لهذه المادة؟\n\n"
        "إذا ما تريدها بالخطة اكتب 0."
    )


# =========================================================
# سؤال الأيام
# =========================================================

def ask_days(user_id):

    users[user_id]["state"] = "waiting_days"

    send_message(

        user_id,

        "🎯 ممتاز!\n\n"
        "هسه اكتب عدد الأيام اللي تريد "
        "تخلص خلالها كل المحاضرات.\n\n"
        "مثلاً:\n"
        "7\n"
        "14\n"
        "30\n"
        "60"
    )


# =========================================================
# إنشاء الخطة
# =========================================================

def generate_plan(user_id):

    user = users[user_id]

    selected = user["subjects"]

    days = user["days"]

    result = create_fixed_plan(
        selected,
        days
    )

    user["result"] = result

    text = format_plan(
        selected,
        days,
        result
    )

    keyboard = [[

        {
            "text": "↩️ تعديل الخطة",
            "callback_data": "reset_plan"
        }

    ]]

    send_message(
        user_id,
        text,
        keyboard
    )

    user["state"] = "finished"


# =========================================================
# /start
# =========================================================

def start_user(chat_id):

    users[chat_id] = {

        "state": "waiting_branch",

        "branch": None,

        "subjects": [],

        "subject_index": 0,

        "current_subject": None,

        "days": None,

        "result": None

    }

    send_message(

        chat_id,

        "📚 أهلاً بك في مخطط أكاديمية السادس\n\n"
        "حدد الفرع حتى نبدأ بإنشاء جدولك الدراسي "
        "الأسبوعي الثابت 🔥",

        branch_keyboard()

    )


# =========================================================
# معالجة الرسائل
# =========================================================

def handle_message(message):

    if "chat" not in message:

        return

    chat_id = message["chat"]["id"]

    text = message.get("text", "").strip()

    if text == "/start":

        start_user(chat_id)

        return

    if chat_id not in users:

        start_user(chat_id)

        return

    user = users[chat_id]

    state = user["state"]


    # ============================================
    # انتظار عدد محاضرات المادة
    # ============================================

    if state == "waiting_lectures":

        try:

            count = int(text)

            if count < 0:

                raise ValueError

        except:

            send_message(

                chat_id,

                "❌ اكتب رقم صحيح فقط.\n"
                "مثلاً: 30\n"
                "أو 0 إذا ما تريد المادة."
            )

            return


        subject = user["current_subject"]

        if count > 0:

            user["subjects"].append({

                "name": subject,

                "count": count

            })


        user["subject_index"] += 1

        ask_next_subject(chat_id)

        return


    # ============================================
    # انتظار عدد الأيام
    # ============================================

    if state == "waiting_days":

        try:

            days = int(text)

            if days < 1:

                raise ValueError

        except:

            send_message(

                chat_id,

                "❌ اكتب عدد أيام صحيح.\n"
                "مثلاً: 7 أو 14 أو 30."
            )

            return


        user["days"] = days

        generate_plan(chat_id)

        return


    if state == "finished":

        send_message(

            chat_id,

            "الخطة جاهزة فوق 👆\n\n"
            "إذا تريد تسوي خطة جديدة اضغط "
            "«↩️ تعديل الخطة» أو اكتب /start."
        )

        return


# =========================================================
# معالجة الأزرار
# =========================================================

def handle_callback(callback):

    callback_id = callback["id"]

    chat_id = callback["message"]["chat"]["id"]

    data = callback["data"]

    telegram(

        "answerCallbackQuery",

        {
            "callback_query_id": callback_id
        }

    )


    # ============================================
    # العلمي
    # ============================================

    if data == "branch_scientific":

        users[chat_id] = {

            "state": "waiting_lectures",

            "branch": "scientific",

            "subjects": [],

            "subject_index": 0,

            "current_subject": None,

            "days": None,

            "result": None

        }

        telegram(

            "editMessageText",

            {
                "chat_id": chat_id,
                "message_id": callback["message"]["message_id"],
                "text":
                    "🔬 تم اختيار السادس العلمي.\n\n"
                    "هسه راح نسألك عن عدد المحاضرات "
                    "لكل مادة."
            }

        )

        ask_next_subject(chat_id)

        return


    # ============================================
    # الأدبي
    # ============================================

    if data == "branch_literary":

        users[chat_id] = {

            "state": "waiting_lectures",

            "branch": "literary",

            "subjects": [],

            "subject_index": 0,

            "current_subject": None,

            "days": None,

            "result": None

        }

        telegram(

            "editMessageText",

            {
                "chat_id": chat_id,
                "message_id": callback["message"]["message_id"],
                "text":
                    "📖 تم اختيار السادس الأدبي.\n\n"
                    "هسه راح نسألك عن عدد المحاضرات "
                    "لكل مادة."
            }

        )

        ask_next_subject(chat_id)

        return


    # ============================================
    # إعادة الخطة
    # ============================================

    if data == "reset_plan":

        start_user(chat_id)

        return


# =========================================================
# Polling
# =========================================================

def run_bot():

    print("================================")
    print("🤖 البوت يعمل الآن...")
    print("اضغط Ctrl+C لإيقافه")
    print("================================")

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

            response = telegram(
                "getUpdates",
                data
            )

            if not response:

                time.sleep(2)
                continue

            if not response.get("ok"):

                print("Telegram API Error:", response)

                time.sleep(5)

                continue


            for update in response["result"]:

                offset = update["update_id"] + 1

                if "message" in update:

                    handle_message(
                        update["message"]
                    )

                elif "callback_query" in update:

                    handle_callback(
                        update["callback_query"]
                    )


        except KeyboardInterrupt:

            print("\nتم إيقاف البوت.")

            break


        except Exception as e:

            print("ERROR:", e)

            time.sleep(5)


# =========================================================
# تشغيل
# =========================================================

if __name__ == "__main__":

    run_bot()