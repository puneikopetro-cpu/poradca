"""
FinAdvisor SK — Telegram Bot

Команди:
  /start       — привітання + меню
  /analyze     — запуск фінансової анкети (крок за кроком)
  /recommend   — отримати рекомендації (якщо анкета заповнена)
  /tip         — фінансовий tip дня
  /contact     — контакти консультанта
  /help        — список команд

Запуск:
  export TELEGRAM_BOT_TOKEN=your_token_here
  export API_BASE=http://localhost:8000
  python telegram_bot/bot.py
"""
from __future__ import annotations
import os
import logging
import urllib.request
import urllib.parse
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_BASE  = os.getenv("API_BASE", "http://localhost:8000")

# Conversation states
(ASK_NAME, ASK_EMAIL, ASK_PHONE, ASK_INCOME, ASK_EXPENSES,
 ASK_SAVINGS, ASK_DEBT, ASK_AGE, ASK_EXPERIENCE, ASK_HORIZON, ASK_GOAL) = range(11)

TIPS = [
    "💡 III. pilier: vkladajte €25/mes → štát pridá €180/rok zadarmo.",
    "📈 ETF MSCI World historicky rastie ~8%/rok. Lepšie ako väčšina fondov.",
    "🏠 Pred hypotékou porovnajte aspoň 5 bánk. Rozdiel môže byť €100/mes.",
    "🧾 Daňová sadzba 19% platí do €41 445 ročne. Nad to je 25%.",
    "🏦 II. pilier: ak máte pod 40 rokov, presuňte sa do indexového fondu.",
    "💳 Splaťte najskôr úver s najvyšším úrokom — ušetríte na poplatkoch.",
]

_tip_index = 0


def api_post(path: str, data: dict) -> dict | None:
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body,
                                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        logger.error("API error %s: %s", path, e)
        return None


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📊 Finančná analýza"), KeyboardButton("💡 Tip dňa")],
        [KeyboardButton("📞 Kontakt"), KeyboardButton("❓ Pomoc")],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Vitajte v *FinAdvisor SK*!\n\n"
        "Som váš digitálny finančný asistent.\n\n"
        "Pomôžem vám s:\n"
        "📈 Investíciami\n🏠 Hypotékou\n🏦 II/III pilierom\n🧾 Daňami\n\n"
        "Vyberte možnosť alebo napíšte /analyze",
        parse_mode="Markdown",
        reply_markup=markup,
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Dostupné príkazy:*\n\n"
        "/start — hlavné menu\n"
        "/analyze — finančná analýza (krok za krokom)\n"
        "/tip — finančný tip dňa\n"
        "/contact — kontakt konzultanta\n"
        "/help — táto správa",
        parse_mode="Markdown",
    )


async def contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Kontakt na konzultanta:*\n\n"
        "✉️ info@finadvisor.sk\n"
        "🌐 finadvisor.sk\n"
        "📱 Telegram: @finadvisor\\_sk\n\n"
        "_Prvá konzultácia je zadarmo._",
        parse_mode="Markdown",
    )


async def tip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global _tip_index
    t = TIPS[_tip_index % len(TIPS)]
    _tip_index += 1
    await update.message.reply_text(f"*Tip dňa:*\n\n{t}", parse_mode="Markdown")


# ── Conversation: Financial Analysis ─────────────────────────────────────────

async def analyze_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "📊 *Finančná analýza*\n\nZačíname! Odpovedzte na niekoľko otázok.\n\n"
        "Ako sa voláte? _(Meno Priezvisko)_",
        parse_mode="Markdown",
    )
    return ASK_NAME


async def got_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("📧 Váš email?")
    return ASK_EMAIL


async def got_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["email"] = update.message.text.strip()
    await update.message.reply_text("📱 Telefón? _(napr. +421 900 000 000)_ alebo napíšte _preskočiť_", parse_mode="Markdown")
    return ASK_PHONE


async def got_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    ctx.user_data["phone"] = "" if val.lower() == "preskočiť" else val
    await update.message.reply_text("💰 Mesačný príjem (€)? Napíšte číslo, napr. _2500_", parse_mode="Markdown")
    return ASK_INCOME


async def got_income(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["monthly_income"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("⚠️ Zadajte číslo, napr. 2500")
        return ASK_INCOME
    await update.message.reply_text("💳 Mesačné výdavky (€)?")
    return ASK_EXPENSES


async def got_expenses(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["monthly_expenses"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("⚠️ Zadajte číslo, napr. 1500")
        return ASK_EXPENSES
    await update.message.reply_text("🏦 Celkové úspory (€)? _(napíšte 0 ak nemáte)_", parse_mode="Markdown")
    return ASK_SAVINGS


async def got_savings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["total_savings"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("⚠️ Zadajte číslo, napr. 5000")
        return ASK_SAVINGS
    await update.message.reply_text("💳 Celkový dlh (€)? _(úvery, hypotéka atď. — napíšte 0 ak nemáte)_", parse_mode="Markdown")
    return ASK_DEBT


async def got_debt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["total_debt"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("⚠️ Zadajte číslo")
        return ASK_DEBT
    await update.message.reply_text("🎂 Koľko máte rokov?")
    return ASK_AGE


async def got_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["age"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ Zadajte celé číslo, napr. 32")
        return ASK_AGE
    keyboard = [["0 rokov", "1-3 roky"], ["4+ rokov"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("📈 Skúsenosti s investovaním?", reply_markup=markup)
    return ASK_EXPERIENCE


async def got_experience(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {"0 rokov": 0, "1-3 roky": 2, "4+ rokov": 5}
    ctx.user_data["investment_experience"] = mapping.get(update.message.text, 0)
    keyboard = [["Krátkodobý (< 2r)", "Strednodobý (2-5r)"], ["Dlhodobý (5r+)"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⏳ Investičný horizont?", reply_markup=markup)
    return ASK_HORIZON


async def got_horizon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {"Krátkodobý (< 2r)": "short", "Strednodobý (2-5r)": "medium", "Dlhodobý (5r+)": "long"}
    ctx.user_data["investment_horizon"] = mapping.get(update.message.text, "medium")
    keyboard = [["Sporenie", "Dôchodok"], ["Nehnuteľnosť", "Vzdelanie"], ["Rast"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🎯 Váš hlavný finančný cieľ?", reply_markup=markup)
    return ASK_GOAL


async def got_goal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {
        "Sporenie": "savings", "Dôchodok": "retirement",
        "Nehnuteľnosť": "property", "Vzdelanie": "education", "Rast": "growth",
    }
    ctx.user_data["goal_type"] = mapping.get(update.message.text, "savings")

    # Save lead to API
    lead_data = {
        "full_name": ctx.user_data.get("full_name", ""),
        "email": ctx.user_data.get("email", ""),
        "phone": ctx.user_data.get("phone", ""),
        "interest": ctx.user_data.get("goal_type", "investment"),
        "message": f"Telegram lead — príjem: €{ctx.user_data.get('monthly_income',0)}/mes",
        "source": "telegram",
    }
    api_post("/leads", lead_data)

    # Calculate risk score locally (simple)
    age = ctx.user_data.get("age", 40)
    cashflow = ctx.user_data.get("monthly_income", 0) - ctx.user_data.get("monthly_expenses", 0)
    exp = ctx.user_data.get("investment_experience", 0)
    horizon = ctx.user_data.get("investment_horizon", "medium")

    score = 0
    score += 25 if age < 35 else (15 if age <= 50 else 5)
    score += 25 if cashflow > 1000 else (15 if cashflow >= 500 else 5)
    score += 25 if exp >= 4 else (15 if exp >= 1 else 5)
    score += 25 if horizon == "long" else (15 if horizon == "medium" else 5)

    if score >= 70:
        profile = "🔴 Agresívny"
        advice = "Odporúčame ETF small cap, individuálne akcie, vyššie riziko/výnos."
    elif score >= 40:
        profile = "🟡 Vyvážený"
        advice = "Odporúčame MSCI World ETF, optimalizáciu II. piliera."
    else:
        profile = "🟢 Konzervatívny"
        advice = "Odporúčame III. pilier (DDS), štátne dlhopisy, termínovaný vklad."

    await update.message.reply_text(
        f"✅ *Analýza dokončená!*\n\n"
        f"📊 Váš rizikový profil: *{profile}* (skóre: {score}/100)\n\n"
        f"💡 {advice}\n\n"
        f"📩 Kontaktujeme vás na *{ctx.user_data.get('email')}* do 24 hodín s podrobným plánom.\n\n"
        f"Alebo nás kontaktujte priamo: /contact",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Analýza zrušená. Môžete začať znova cez /analyze")
    return ConversationHandler.END


async def menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "analýza" in text.lower() or "Finančná" in text:
        return await analyze_start(update, ctx)
    elif "tip" in text.lower():
        await tip(update, ctx)
    elif "kontakt" in text.lower():
        await contact(update, ctx)
    elif "pomoc" in text.lower():
        await help_cmd(update, ctx)


def main():
    if not BOT_TOKEN:
        raise EnvironmentError("Set TELEGRAM_BOT_TOKEN env variable.")

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("analyze", analyze_start),
            MessageHandler(filters.Regex("📊 Finančná analýza"), analyze_start),
        ],
        states={
            ASK_NAME:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            ASK_EMAIL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_email)],
            ASK_PHONE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone)],
            ASK_INCOME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, got_income)],
            ASK_EXPENSES:   [MessageHandler(filters.TEXT & ~filters.COMMAND, got_expenses)],
            ASK_SAVINGS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_savings)],
            ASK_DEBT:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_debt)],
            ASK_AGE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, got_age)],
            ASK_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_experience)],
            ASK_HORIZON:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_horizon)],
            ASK_GOAL:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_goal)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    return app


async def build_application(token: str) -> Application:
    """Build and initialize app for webhook mode (used by FastAPI)."""
    app = Application.builder().token(token).build()
    _register_handlers(app)
    await app.initialize()
    return app


def _register_handlers(app: Application):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("analyze", analyze_start),
            MessageHandler(filters.Regex("📊 Finančná analýza"), analyze_start),
        ],
        states={
            ASK_NAME:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            ASK_EMAIL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_email)],
            ASK_PHONE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone)],
            ASK_INCOME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, got_income)],
            ASK_EXPENSES:   [MessageHandler(filters.TEXT & ~filters.COMMAND, got_expenses)],
            ASK_SAVINGS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_savings)],
            ASK_DEBT:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_debt)],
            ASK_AGE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, got_age)],
            ASK_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_experience)],
            ASK_HORIZON:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_horizon)],
            ASK_GOAL:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_goal)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))


def main():
    if not BOT_TOKEN:
        raise EnvironmentError("Set TELEGRAM_BOT_TOKEN env variable.")

    app = Application.builder().token(BOT_TOKEN).build()
    _register_handlers(app)

    logger.info("Bot started (polling mode). Listening...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
