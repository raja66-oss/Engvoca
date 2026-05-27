import os
import random
import requests
import difflib
import sqlite3
from datetime import date
from deep_translator import GoogleTranslator
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("8284413656:AAH3lAklbrVhdXn7dwlAPnDg2EOa9bSnTMQ")
NEWS_API_KEY = os.getenv("b3582497a8a7429abcc99f7c3fad95e2")
ADMIN_ID = int(os.getenv("8459676381"))

conn = sqlite3.connect("saha_vocab.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    language TEXT DEFAULT 'bn'
)
""")
conn.commit()

BANKING_WORDS = [
    "abate", "aberration", "abrogate", "acumen", "admonish",
    "affluent", "alleviate", "ambiguous", "amicable", "anomaly",
    "appease", "arbitrary", "arduous", "assiduous", "austere",
    "benevolent", "candid", "coercive", "cognizant", "complacent",
    "concise", "concur", "conspicuous", "conventional", "credible",
    "dearth", "defer", "diligent", "discrepancy", "elaborate",
    "eloquent", "emulate", "ephemeral", "exemplary", "frugal",
    "gratify", "impartial", "impeccable", "inevitable", "lucid",
    "meticulous", "obscure", "pragmatic", "prolific", "resilient",
    "scrutinize", "tenacious", "viable", "vigilant", "zealous",
    "accompany", "abide", "irritate", "narrative", "attribute",
    "unprecedented", "bonhomie", "tepid", "dominant", "precise",
    "hostile", "optimistic", "pessimistic", "fragile", "robust"
]

COMMON_WORDS = BANKING_WORDS

keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📚 New 5 Words")],
        [KeyboardButton("📚 New 10 Words")],
        [KeyboardButton("📰 Today Editorial")],
        [KeyboardButton("🌐 Change Language")],
        [KeyboardButton("👥 Total Users")]
    ],
    resize_keyboard=True
)

language_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Bengali"), KeyboardButton("Hindi")],
        [KeyboardButton("Tamil"), KeyboardButton("Telugu")],
        [KeyboardButton("Other Language")],
        [KeyboardButton("⬅ Back")]
    ],
    resize_keyboard=True
)

other_language_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Marathi"), KeyboardButton("Urdu")],
        [KeyboardButton("Gujarati"), KeyboardButton("Malayalam")],
        [KeyboardButton("Kannada"), KeyboardButton("Punjabi")],
        [KeyboardButton("⬅ Back")]
    ],
    resize_keyboard=True
)

LANG_MAP = {
    "bengali": "bn",
    "hindi": "hi",
    "tamil": "ta",
    "telugu": "te",
    "marathi": "mr",
    "urdu": "ur",
    "gujarati": "gu",
    "malayalam": "ml",
    "kannada": "kn",
    "punjabi": "pa"
}


def add_user(user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()


def get_user_language(user_id):
    cursor.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else "bn"


def set_user_language(user_id, lang):
    cursor.execute(
        "UPDATE users SET language=? WHERE user_id=?",
        (lang, user_id)
    )
    conn.commit()


def get_total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]


def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source="en", target=target_lang).translate(text)
    except Exception:
        return "Translation unavailable."


def get_word_data(word, target_lang):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()[0]

        best_meaning = None
        best_definition = None

        for meaning in data.get("meanings", []):
            for d in meaning.get("definitions", []):
                definition = d.get("definition", "")
                bad = ["musical scale", "tone of a musical"]
                if len(definition) > 20 and not any(x in definition.lower() for x in bad):
                    best_meaning = meaning
                    best_definition = d
                    break
            if best_definition:
                break

        if not best_meaning:
            best_meaning = data["meanings"][0]
            best_definition = best_meaning["definitions"][0]

        part = best_meaning.get("partOfSpeech", "N/A")
        definition = best_definition.get("definition", "No definition found.")
        example = best_definition.get("example", "No example available.")

        synonyms = []
        synonyms.extend(best_meaning.get("synonyms", []))
        synonyms.extend(best_definition.get("synonyms", []))
        synonyms = list(dict.fromkeys(synonyms))[:5]

        if not synonyms:
            synonyms = difflib.get_close_matches(word, COMMON_WORDS, n=5, cutoff=0.35)

        translated_word = translate_text(word, target_lang)
        translated_meaning = translate_text(definition, target_lang)

        return word, translated_word, part, definition, translated_meaning, example, synonyms

    except Exception:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)

    welcome_text = """
╔════════════════════╗
      ✨ 𝗦𝗔𝗛𝗔 𝗩𝗢𝗖𝗔𝗕 ✨
╚════════════════════╝

🎓 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢
𝗧𝗛𝗘 𝗨𝗟𝗧𝗜𝗠𝗔𝗧𝗘
𝗩𝗢𝗖𝗔𝗕𝗨𝗟𝗔𝗥𝗬 𝗕𝗢𝗧

🚀 Improve Your:
🔹 Banking English
🔹 Vocabulary Power
🔹 English Fluency
🔹 Competitive Exam English

📖 Send Any English Word

🌍 English meaning compulsory
🪷 Choose your translation language

👇 Use Buttons Below 👇
"""
    await update.message.reply_text(welcome_text, reply_markup=keyboard)


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await update.message.reply_text(
        f"🆔 Your Telegram Details\n\n"
        f"👤 Name: {user.first_name}\n"
        f"📌 Username: @{user.username}\n"
        f"🆔 User ID: {user.id}"
    )


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 Choose your default meaning language:",
        reply_markup=language_keyboard
    )


async def send_words(update, count):
    user_id = update.effective_user.id
    target_lang = get_user_language(user_id)

    today_seed = str(date.today()) + str(count)
    random.seed(today_seed)
    words = random.sample(BANKING_WORDS, count)

    reply = f"📚 𝗧𝗼𝗱𝗮𝘆'𝘀 {count} 𝗕𝗮𝗻𝗸𝗶𝗻𝗴 𝗩𝗼𝗰𝗮𝗯 𝗪𝗼𝗿𝗱𝘀\n\n"

    for i, word in enumerate(words, start=1):
        data = get_word_data(word, target_lang)

        if data:
            w, tw, part, eng, trans, example, synonyms = data
            similar_words = ", ".join(synonyms) if synonyms else "Not available"

            reply += (
                f"{i}. 📘 {w.title()}\n"
                f"🔤 Translation: {tw}\n"
                f"📌 Part Of Speech: {part}\n"
                f"🌍 English Meaning:\n{eng}\n"
                f"🪷 Translation:\n{trans}\n"
                f"🧩 Similar Words: {similar_words}\n"
                f"✍️ Example: {example}\n\n"
            )

    await update.message.reply_text(reply, reply_markup=keyboard)


async def today_editorial(update):
    try:
        user_id = update.effective_user.id
        target_lang = get_user_language(user_id)

        url = (
            f"https://newsapi.org/v2/everything?"
            f"q=banking OR economy OR finance"
            f"&language=en"
            f"&sortBy=publishedAt"
            f"&pageSize=20"
            f"&apiKey={NEWS_API_KEY}"
        )

        response = requests.get(url, timeout=10).json()
        articles = response.get("articles", [])

        if not articles:
            await update.message.reply_text("❌ No editorial found today.", reply_markup=keyboard)
            return

        article = random.choice(articles)

        title = article.get("title") or "Today's Editorial"
        content = article.get("content") or ""
        description = article.get("description") or ""

        full_passage = f"""
{description}

{content}

This topic is important for banking and competitive examination aspirants because it improves reading comprehension, vocabulary, analytical ability and current affairs awareness.

Students should focus on:
• Main issue
• Causes
• Economic impact
• Government policies
• Possible solutions

Daily editorial reading greatly improves English fluency and exam preparation.
"""

        translated = translate_text(full_passage, target_lang)

        reply = f"""
📰 𝗧𝗢𝗗𝗔𝗬 𝗘𝗗𝗜𝗧𝗢𝗥𝗜𝗔𝗟

📌 𝗧𝗶𝘁𝗹𝗲:
{title}

🌍 𝗘𝗻𝗴𝗹𝗶𝘀𝗵 𝗣𝗮𝘀𝘀𝗮𝗴𝗲:
{full_passage}

🪷 𝗧𝗿𝗮𝗻𝘀𝗹𝗮𝘁𝗶𝗼𝗻:
{translated}
"""
        await update.message.reply_text(reply, reply_markup=keyboard)

    except Exception:
        await update.message.reply_text("❌ Editorial unavailable today.", reply_markup=keyboard)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("Usage:\n/broadcast your message")
        return

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    success = 0
    failed = 0

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user[0],
                text=f"📢 𝗔𝗗𝗠𝗜𝗡 𝗠𝗘𝗦𝗦𝗔𝗚𝗘\n\n{msg}"
            )
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast Complete\n\nSent: {success}\nFailed: {failed}"
    )


async def total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can check total users.")
        return

    await update.message.reply_text(f"👥 Total Bot Users: {get_total_users()}")


async def meaning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    text = update.message.text.strip().lower()

    if text == "📚 new 5 words":
        await send_words(update, 5)
        return

    if text == "📚 new 10 words":
        await send_words(update, 10)
        return

    if text == "📰 today editorial":
        await today_editorial(update)
        return

    if text == "🌐 change language":
        await change_language(update, context)
        return

    if text == "👥 total users":
        await total_users(update, context)
        return

    if text == "other language":
        await update.message.reply_text(
            "🌍 Choose other language:",
            reply_markup=other_language_keyboard
        )
        return

    if text == "⬅ back":
        await update.message.reply_text(
            "✅ Back to main menu",
            reply_markup=keyboard
        )
        return

    if text in LANG_MAP:
        lang_code = LANG_MAP[text]
        set_user_language(user_id, lang_code)

        await update.message.reply_text(
            f"✅ Default language changed to: {text.title()}",
            reply_markup=keyboard
        )
        return

    target_lang = get_user_language(user_id)
    data = get_word_data(text, target_lang)

    if data:
        w, tw, part, eng, trans, example, synonyms = data
        similar_words = ", ".join(synonyms) if synonyms else "Not available"

        reply = f"""
📘 𝗪𝗼𝗿𝗱:
{w.title()}

🔤 𝗧𝗿𝗮𝗻𝘀𝗹𝗮𝘁𝗶𝗼𝗻:
{tw}

📌 𝗣𝗮𝗿𝘁 𝗢𝗳 𝗦𝗽𝗲𝗲𝗰𝗵:
{part}

🌍 𝗘𝗻𝗴𝗹𝗶𝘀𝗵 𝗠𝗲𝗮𝗻𝗶𝗻𝗴:
{eng}

🪷 𝗧𝗿𝗮𝗻𝘀𝗹𝗮𝘁𝗶𝗼𝗻:
{trans}

🧩 𝗦𝗶𝗺𝗶𝗹𝗮𝗿 𝗘𝗻𝗴𝗹𝗶𝘀𝗵 𝗪𝗼𝗿𝗱𝘀:
{similar_words}

✍️ 𝗘𝘅𝗮𝗺𝗽𝗹𝗲:
{example}
"""
        await update.message.reply_text(reply, reply_markup=keyboard)

    else:
        suggestions = difflib.get_close_matches(text, COMMON_WORDS, n=3, cutoff=0.55)

        if suggestions:
            suggest_text = "\n".join([f"👉 {w}" for w in suggestions])
            await update.message.reply_text(
                f"❌ Word Not Found\n\nDid You Mean?\n\n{suggest_text}",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                "❌ Word Not Found.\nTry another English word.",
                reply_markup=keyboard
            )


if not TOKEN:
    raise ValueError("TOKEN missing in Railway Variables")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", myid))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, meaning))

print("✅ SAHA VOCAB Bot Running...")
app.run_polling()
