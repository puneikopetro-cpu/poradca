"""
FinAdvisor SK — Telegram Bot

Prikazy:
  /start       — vitanie + menu
  /help        — zoznam prikazov
  /investovat  — info o investicnych sluzbách
  /hypoteka    — info o hypotekach
  /kontakt     — kontaktne informacie
  /analyze     — spustenie financnej analyzy (krok za krokom)
  /recommend   — odporucania (ak je anketa vyplnena)
  /tip         — financny tip dna

Spustenie:
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

SITE_CTA = "\n\n💬 *Chcete bezplatnu konzultaciu?* Napiste na https://finadvisor.sk"

# Conversation states
(ASK_NAME, ASK_EMAIL, ASK_PHONE, ASK_INCOME, ASK_EXPENSES,
 ASK_SAVINGS, ASK_DEBT, ASK_AGE, ASK_EXPERIENCE, ASK_HORIZON, ASK_GOAL) = range(11)

TIPS = [
    "💡 III. pilier: vkladajte €25/mes → stat prida €180/rok zadarmo.",
    "📈 ETF MSCI World historicky rastie ~8%/rok. Lepsie ako vacsina fondov.",
    "🏠 Pred hypotekou porovnajte aspon 5 bank. Rozdiel moze byt €100/mes.",
    "🧾 Danova sadzba 19% plati do €41 445 rocne. Nad to je 25%.",
    "🏦 II. pilier: ak mate pod 40 rokov, presunite sa do indexoveho fondu.",
    "💳 Splafte najskor uver s najvyssim urokom — usetryte na poplatkoch.",
]

_tip_index = 0


def api_post(path: str, data: dict):
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


def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📊 Financna analyza"), KeyboardButton("💡 Tip dna")],
        [KeyboardButton("📈 Investovanie"), KeyboardButton("🏠 Hypoteka")],
        [KeyboardButton("📞 Kontakt"), KeyboardButton("❓ Pomoc")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    markup = get_main_keyboard()
    await update.message.reply_text(
        "👋 Vitajte v *FinAdvisor SK*!\n\n"
        "Som vas digitalny financny asistent pre Slovensko.\n\n"
        "Pomozem vam s:\n"
        "📈 *Investiciami a ETF fondmi*\n"
        "🏠 *Hypotekami a uvermi*\n"
        "🛡️ *Poistenim*\n"
        "💰 *Danovymi optimalizaciami*\n"
        "🎯 *Financnym plánovanim*\n\n"
        "Vyberte temu alebo pouzite /help pre zoznam vsetkych prikazov."
        + SITE_CTA,
        parse_mode="Markdown",
        reply_markup=markup,
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Dostupne prikazy:*\n\n"
        "/start — hlavne menu\n"
        "/investovat — info o investovani a ETF\n"
        "/hypoteka — info o hypotekach\n"
        "/kontakt — kontakty konzultanta\n"
        "/analyze — financna analyza (krok za krokom)\n"
        "/tip — financny tip dna\n"
        "/help — tato sprava"
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def cmd_investovat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 *Investovanie & ETF fondy*\n\n"
        "Pomozeme vam nastavit investicnu strategiu presne podla vasich cielov a rizikoveho profilu.\n\n"
        "*Co ponukame:*\n"
        "• Diverzifikovane ETF portfoio (MSCI World, S&P 500)\n"
        "• II. pilier — optimalizacia fondu\n"
        "• III. pilier — danove uroky az €180/rok od statu\n"
        "• Nezavisle poradenstvo — nepredavame konkretne produkty\n\n"
        "*Preco ETF?*\n"
        "Historicky rast ~8%/rok, nizke poplatky (0.07-0.2%/rok), plna transparentnost.\n\n"
        "_Prvy krok je vzdy bezplatny._"
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def cmd_hypoteka(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 *Hypoteky & Uvery*\n\n"
        "Porovnanie hypotek od vsetkych hlavnych slovenskych bank — SLSP, VUB, Tatra, mBank a dalsich.\n\n"
        "*Nase sluzby:*\n"
        "• Bezplatne porovnanie ponuk vsetkych bank\n"
        "• Vypocet optimálnej vysky splátky\n"
        "• Pomoc s dokumentáciou a zariadenim\n"
        "• Refinancovanie existujucej hypoteky\n\n"
        "*Tip:* Rozdiel medzi najlepsou a najhorsou ponukou moze byt az €100/mes = €12 000 za 10 rokov!\n\n"
        "_Poziadajte o bezplatnu analyzu hypoteky._"
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Kontakt na konzultanta:*\n\n"
        "✉️ petropuneiko@gmail.com\n"
        "📱 +421 908 118 957\n"
        "🌐 finadvisor.sk\n"
        "🤖 Telegram: @finadvisor\\_sk\\_bot\n\n"
        "_Prvá konzultacia je zadarmo. Odpovieme do 24 hodin._",
        parse_mode="Markdown",
    )


async def tip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global _tip_index
    t = TIPS[_tip_index % len(TIPS)]
    _tip_index += 1
    await update.message.reply_text(
        f"*Tip dna:*\n\n{t}"
        + SITE_CTA,
        parse_mode="Markdown",
    )


# ── Keyword-based smart responses ─────────────────────────────────────────────

KEYWORD_RESPONSES = {
    # Investment keywords
    ("investici", "investovat", "etf", "akcie", "portfoio", "portfólio", "fond", "sporeni", "sporit"): "invest",
    # Mortgage keywords
    ("hypoteka", "hypotéka", "uver", "úver", "banka", "splátka", "nehnutelnost", "nehnuteľnosť", "byt", "dom", "kupim"): "mortgage",
    # Insurance keywords
    ("poistenie", "poisťovnia", "poistit", "poistiť", "zivotne", "životné", "majetkove", "majetkové", "uraz", "úraz"): "insurance",
    # Tax keywords
    ("dan", "daň", "danove", "daňové", "odpocet", "odpočet", "ii. pilier", "iii. pilier", "pilier", "danovník"): "tax",
    # Greeting keywords
    ("ahoj", "zdravim", "dobrý", "dobry", "cau", "ciao", "hello", "hi"): "greeting",
    # Help keywords
    ("pomoc", "pomoct", "pomôct", "co robite", "čo robíte", "sluzby", "služby", "ponuka"): "help_info",
}


async def smart_response(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower() if update.message.text else ""

    matched_type = None
    for keywords, resp_type in KEYWORD_RESPONSES.items():
        if any(kw in text for kw in keywords):
            matched_type = resp_type
            break

    if matched_type == "invest":
        await cmd_investovat(update, ctx)
    elif matched_type == "mortgage":
        await cmd_hypoteka(update, ctx)
    elif matched_type == "insurance":
        await update.message.reply_text(
            "🛡️ *Poistenie*\n\n"
            "Spravne poistenie vam usetri financne straty v neocakavanych situaciach.\n\n"
            "*Druhy poistenia:*\n"
            "• Zivotne poistenie — ochrana rodiny\n"
            "• Majetkove poistenie — byt, dom, auto\n"
            "• Zodpovednostne poistenie\n"
            "• PZP a havarijne poistenie\n\n"
            "Porovname ponuky vsetkych poisticovni a najdeme najlepsiu cenu pre vas."
            + SITE_CTA,
            parse_mode="Markdown",
        )
    elif matched_type == "tax":
        await update.message.reply_text(
            "💰 *Danove optimalizacie*\n\n"
            "Legalne znizenie vasho danoveno zatazenia — zakonite a bezpecne.\n\n"
            "*Co mozeme optimalizovat:*\n"
            "• II. pilier — vhodny indexovy fond\n"
            "• III. pilier — stat prida az €180/rok\n"
            "• Odratatelne polozky zo zakladu dane\n"
            "• Danove priznanie — pomoc s vyplnanim\n"
            "• Optimalizacia pre zivnostnikov a SRO\n\n"
            "_Priemerny klient usetrí €300-800/rok na daniach._"
            + SITE_CTA,
            parse_mode="Markdown",
        )
    elif matched_type == "greeting":
        await start(update, ctx)
    elif matched_type == "help_info":
        await help_cmd(update, ctx)
    else:
        # Generic fallback
        await update.message.reply_text(
            "Dakujem za spravu! 🙏\n\n"
            "Mam odpovede na otazky tykajuce sa:\n"
            "📈 /investovat — Investovanie a ETF\n"
            "🏠 /hypoteka — Hypoteky a uvery\n"
            "📊 /analyze — Osobna financna analyza\n"
            "📞 /kontakt — Kontakt\n\n"
            "Pre odbornu konzultaciu navstivte nas:"
            + SITE_CTA,
            parse_mode="Markdown",
        )


# ── Conversation: Financial Analysis ──────────────────────────────────────────

async def analyze_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "📊 *Financna analyza*\n\nZaciname! Odpovedzte na niekolko otazok.\n\n"
        "Ako sa voláte? _(Meno Priezvisko)_",
        parse_mode="Markdown",
    )
    return ASK_NAME


async def got_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("📧 Vas email?")
    return ASK_EMAIL


async def got_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["email"] = update.message.text.strip()
    await update.message.reply_text("📱 Telefon? _(napr. +421 900 000 000)_ alebo napiste _preskocit_", parse_mode="Markdown")
    return ASK_PHONE


async def got_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    ctx.user_data["phone"] = "" if val.lower() == "preskocit" else val
    await update.message.reply_text("💰 Mesacny prijem (€)? Napiste cislo, napr. _2500_", parse_mode="Markdown")
    return ASK_INCOME


async def got_income(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["monthly_income"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte cislo, napr. 2500")
        return ASK_INCOME
    await update.message.reply_text("💳 Mesacne vydavky (€)?")
    return ASK_EXPENSES


async def got_expenses(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["monthly_expenses"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte cislo, napr. 1500")
        return ASK_EXPENSES
    await update.message.reply_text("🏦 Celkove uspory (€)? _(napiste 0 ak nemate)_", parse_mode="Markdown")
    return ASK_SAVINGS


async def got_savings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["total_savings"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte cislo, napr. 5000")
        return ASK_SAVINGS
    await update.message.reply_text("💳 Celkovy dlh (€)? _(uvery, hypoteka atd. — napiste 0 ak nemate)_", parse_mode="Markdown")
    return ASK_DEBT


async def got_debt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["total_debt"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte cislo")
        return ASK_DEBT
    await update.message.reply_text("Kolko mate rokov?")
    return ASK_AGE


async def got_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["age"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Zadajte cele cislo, napr. 32")
        return ASK_AGE
    keyboard = [["0 rokov", "1-3 roky"], ["4+ rokov"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("📈 Skusenosti s investovanim?", reply_markup=markup)
    return ASK_EXPERIENCE


async def got_experience(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {"0 rokov": 0, "1-3 roky": 2, "4+ rokov": 5}
    ctx.user_data["investment_experience"] = mapping.get(update.message.text, 0)
    keyboard = [["Kratkodoby (< 2r)", "Strednodoby (2-5r)"], ["Dlhodoby (5r+)"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Investicny horizont?", reply_markup=markup)
    return ASK_HORIZON


async def got_horizon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {"Kratkodoby (< 2r)": "short", "Strednodoby (2-5r)": "medium", "Dlhodoby (5r+)": "long"}
    ctx.user_data["investment_horizon"] = mapping.get(update.message.text, "medium")
    keyboard = [["Sporenie", "Dochodok"], ["Nehnutelnost", "Vzdelanie"], ["Rast"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Vas hlavny financny ciel?", reply_markup=markup)
    return ASK_GOAL


async def got_goal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {
        "Sporenie": "savings", "Dochodok": "retirement",
        "Nehnutelnost": "property", "Vzdelanie": "education", "Rast": "growth",
    }
    ctx.user_data["goal_type"] = mapping.get(update.message.text, "savings")

    lead_data = {
        "full_name": ctx.user_data.get("full_name", ""),
        "email": ctx.user_data.get("email", ""),
        "phone": ctx.user_data.get("phone", ""),
        "interest": ctx.user_data.get("goal_type", "investment"),
        "message": f"Telegram lead — prijem: €{ctx.user_data.get('monthly_income', 0)}/mes",
        "source": "telegram",
    }
    api_post("/leads", lead_data)

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
        profile = "Agresivny"
        advice = "Odporucame ETF small cap, individualne akcie, vyssie riziko/vynos."
    elif score >= 40:
        profile = "Vyvazeny"
        advice = "Odporucame MSCI World ETF, optimalizaciu II. piliera."
    else:
        profile = "Konzervativny"
        advice = "Odporucame III. pilier (DDS), statne dlhopisy, terminovany vklad."

    await update.message.reply_text(
        f"Analyza dokoncena!\n\n"
        f"Vas rizikovy profil: *{profile}* (skore: {score}/100)\n\n"
        f"{advice}\n\n"
        f"Kontaktujeme vas na *{ctx.user_data.get('email')}* do 24 hodin s podrobnym planom.\n\n"
        f"Alebo nas kontaktujte priamo: /kontakt"
        + SITE_CTA,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Analyza zrusena. Mozete zacat znova cez /analyze", reply_markup=get_main_keyboard())
    return ConversationHandler.END


async def menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    text_lower = text.lower()

    if "financna analyza" in text_lower or "analyza" in text_lower:
        return await analyze_start(update, ctx)
    elif "tip dna" in text_lower or "tip" in text_lower:
        await tip(update, ctx)
    elif "kontakt" in text_lower:
        await contact(update, ctx)
    elif "pomoc" in text_lower or "help" in text_lower:
        await help_cmd(update, ctx)
    elif "investovanie" in text_lower:
        await cmd_investovat(update, ctx)
    elif "hypoteka" in text_lower:
        await cmd_hypoteka(update, ctx)
    else:
        await smart_response(update, ctx)


def _register_handlers(app: Application):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("analyze", analyze_start),
            MessageHandler(filters.Regex("📊 Financna analyza"), analyze_start),
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
    app.add_handler(CommandHandler("investovat", cmd_investovat))
    app.add_handler(CommandHandler("hypoteka", cmd_hypoteka))
    app.add_handler(CommandHandler("kontakt", contact))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))


async def build_application(token: str) -> Application:
    """Build and initialize app for webhook mode (used by FastAPI)."""
    app = Application.builder().token(token).build()
    _register_handlers(app)
    await app.initialize()
    return app


def main():
    if not BOT_TOKEN:
        raise EnvironmentError("Set TELEGRAM_BOT_TOKEN env variable.")

    app = Application.builder().token(BOT_TOKEN).build()
    _register_handlers(app)

    logger.info("Bot started (polling mode). Listening...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
