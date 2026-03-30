"""
FinAdvisor SK — Telegram Bot (vzdelávacia platforma)

PRÁVNA POZNÁMKA: Tento bot poskytuje výlučne vzdelávacie informácie
v zmysle §1 ods. 2 zákona č. 186/2009 Z.z. Nie je finančným
sprostredkovateľom ani poradcom. Neposkytuje personalizované
finančné odporúčania.

Prikazy:
  /start       — vitanie + menu
  /help        — zoznam prikazov
  /vzdelavanie — vzdelávacie témy
  /kalkulacky  — prehľad kalkulačiek
  /nbs         — príprava na skúšku NBS
  /kontakt     — kontaktné informácie
  /analyze     — finančný IQ dotazník
  /tip         — vzdelávací tip dňa
  /test        — cvičná otázka NBS
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

# Právny disclaimer — povinný pri každej finančnej téme
DISCLAIMER = (
    "\n\n⚠️ _Informácie slúžia výlučne na vzdelávacie účely. "
    "Nie sú finančným poradenstvom v zmysle zákona 186/2009 Z.z. "
    "Pred akýmkoľvek rozhodnutím sa poraďte s licencovaným odborníkom._"
)

SITE_CTA = "\n\n🎓 *Viac vzdelávacích materiálov:* https://finadvisor.sk/learn"

# Conversation states
(ASK_NAME, ASK_EMAIL, ASK_PHONE, ASK_INCOME, ASK_EXPENSES,
 ASK_SAVINGS, ASK_DEBT, ASK_AGE, ASK_EXPERIENCE, ASK_HORIZON, ASK_GOAL) = range(11)

TIPS = [
    "💡 *III. pilier:* Každý, kto vkladá aspoň €1/mes, môže získať príspevok od štátu až €180/rok. Viac: finadvisor.sk/learn",
    "📈 *ETF fondy:* Historický rast MSCI World je ~8%/rok za posledných 30 rokov. Naučte sa ako fungujú: finadvisor.sk/learn",
    "🏠 *Hypotéka:* Vedeli ste, že rozdiel medzi najlepšou a priemernou ponukou banky môže byť €50-150/mes? Naučte sa porovnávať.",
    "🧾 *Dane:* Sadzba 19% platí do €41 445 ročne. Nad túto hranicu je 25%. Vzdelávacia kalkulačka: finadvisor.sk/app",
    "🏦 *II. pilier:* Ak máte pod 40 rokov, zistite ako fungujú indexové fondy v II. pilieri — môže to výrazne ovplyvniť vašu penziu.",
    "💳 *Dlhy:* Princíp lavíny: splácajte najskôr úver s najvyšším úrokom. Ušetríte na poplatkoch. Kalkulačka: finadvisor.sk/app",
    "📊 *Financial IQ:* Otestujte svoje finančné znalosti na finadvisor.sk — bezplatný IQ Score 0-850.",
]

_tip_index = 0


def api_get(path: str):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        logger.error("API GET error %s: %s", path, e)
        return None


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
        [KeyboardButton("🎓 Vzdelávanie"), KeyboardButton("💡 Tip dňa")],
        [KeyboardButton("📊 Finančný IQ test"), KeyboardButton("🏦 NBS príprava")],
        [KeyboardButton("📞 Kontakt"), KeyboardButton("❓ Pomoc")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    markup = get_main_keyboard()
    await update.message.reply_text(
        "👋 Vitajte v *FinAdvisor SK*!\n\n"
        "Som váš vzdelávací sprievodca svetom financií pre Slovensko.\n\n"
        "Pomôžem vám *porozumieť*:\n"
        "📈 Investíciám a ETF fondom\n"
        "🏠 Hypotékam a úverom\n"
        "🛡️ Poisteniu\n"
        "💰 Daniam a II./III. pilier\n"
        "🎯 Finančnému plánovaní\n\n"
        "⚠️ _Tento bot poskytuje vzdelávacie informácie, nie finančné poradenstvo._"
        + SITE_CTA,
        parse_mode="Markdown",
        reply_markup=markup,
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Dostupné príkazy:*\n\n"
        "/start — hlavné menu\n"
        "/vzdelavanie — vzdelávacie témy\n"
        "/kalkulacky — prehľad kalkulačiek\n"
        "/nbs — príprava na skúšku NBS\n"
        "/kontakt — kontaktné informácie\n"
        "/analyze — finančný IQ dotazník\n"
        "/tip — vzdelávací tip dňa\n"
        "/test — cvičná NBS otázka\n"
        "/help — táto správa\n\n"
        "⚠️ _Všetok obsah slúži výlučne na vzdelávacie účely (zákon 186/2009 Z.z.)._"
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def cmd_vzdelavanie(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 *Vzdelávacie témy na FinAdvisor SK*\n\n"
        "*📈 Investície a ETF fondy*\n"
        "Zistite ako fungujú ETF, akcie, dlhopisy. Čo je diverzifikácia, rizikový profil a dlhodobé investovanie.\n\n"
        "*🏠 Hypotéky a úvery*\n"
        "Naučte sa čítať ponuku banky, pochopiť RPMN, fixáciu úroku a refinancovanie.\n\n"
        "*🛡️ Poistenie*\n"
        "Pochopte rozdiel medzi životným, majetkovým a zodpovednostným poistením.\n\n"
        "*💰 Dane a II./III. pilier*\n"
        "Naučte sa ako funguje daňový systém SR, II. a III. pilier dôchodkového sporenia.\n\n"
        "*🎯 Finančné plánovanie*\n"
        "Pravidlo 50/30/20, núdzový fond, finančné ciele krok za krokom."
        + DISCLAIMER
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def cmd_kalkulacky(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔢 *Vzdelávacie kalkulačky na finadvisor.sk/app*\n\n"
        "• 📈 ETF kalkulačka — ako rastie investícia v čase\n"
        "• 🏠 Hypotekárna kalkulačka — mesačná splátka\n"
        "• 💰 Daňová vzdelávacia kalkulačka — odhad dane\n"
        "• 🏦 II. pilier kalkulačka — vplyv fondov\n"
        "• 🎯 III. pilier — príspevok štátu\n"
        "• 📊 Zložené úroky — sila času\n\n"
        "Výsledky kalkulačiek sú *orientačné* a neslúžia ako finančné odporúčanie."
        + DISCLAIMER
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def cmd_nbs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Príprava na skúšku NBS*\n\n"
        "Naša platforma obsahuje *1 334 cvičných otázok* zo zverejnených materiálov NBS "
        "pre finančných sprostredkovateľov (zákon 186/2009 Z.z.).\n\n"
        "*Oblasti prípravy:*\n"
        "• Zákon 186/2009 Z.z. — finančné sprostredkovanie\n"
        "• Zákon 39/2015 Z.z. — poistenie\n"
        "• Zákon 566/2001 Z.z. — cenné papiere\n"
        "• Zákon 90/2016 Z.z. — hypotekárny úver\n"
        "• GDPR a ochrana spotrebiteľa\n\n"
        "📝 Cvičný test teraz: /test\n\n"
        "_Obsah je prípravou na skúšku, nie náhradou licencie NBS._"
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def cmd_investovat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 *Vzdelávanie — Investície & ETF fondy*\n\n"
        "*Čo sú ETF fondy?*\n"
        "ETF (Exchange Traded Fund) je fond obchodovaný na burze, ktorý sleduje index "
        "(napr. S&P 500, MSCI World). Historický rast ~8%/rok za 30 rokov.\n\n"
        "*Prečo dlhodobé investovanie?*\n"
        "Sila zloženého úroku: €100/mes po 30 rokoch pri 8% = ~€136 000.\n\n"
        "*II. pilier — čo treba vedieť:*\n"
        "Môžete si vybrať fond — indexový vs. dlhopisový. Rozhodnutie závisí od veku a "
        "časového horizontu.\n\n"
        "*III. pilier — bonus od štátu:*\n"
        "Pri vklade €25+/mes štát pridá príspevok. Daňový odpočet až €180/rok.\n\n"
        "_Vyskúšajte ETF kalkulačku na finadvisor.sk/app_"
        + DISCLAIMER
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def cmd_hypoteka(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 *Vzdelávanie — Hypotéky & Úvery*\n\n"
        "*Ako čítať ponuku banky:*\n"
        "• Úroková sadzba — ročné % z dlžnej sumy\n"
        "• RPMN — celkové náklady úveru (dôležitejšie ako úrok!)\n"
        "• Fixácia — 1, 3, 5, 10 rokov — stabilita splátky\n\n"
        "*Na čo si dávať pozor:*\n"
        "• Poplatky za poskytnutie, správu, predčasné splatenie\n"
        "• Povinné poistenie — niekedy skryté náklady\n"
        "• LTV (Loan to Value) — max 80-90% ceny nehnuteľnosti\n\n"
        "*Refinancovanie — kedy sa oplatí?*\n"
        "Keď rozdiel v sadzbe > 0.5% a zostatok dlhu > €30 000.\n\n"
        "_Hypotekárna kalkulačka: finadvisor.sk/app_"
        + DISCLAIMER
        + SITE_CTA,
        parse_mode="Markdown",
    )


async def contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Kontakt — FinAdvisor SK*\n\n"
        "✉️ petropuneiko@gmail.com\n"
        "📱 +421 908 118 957\n"
        "🌐 finadvisor.sk\n\n"
        "⏰ Odpovieme do 24 hodín.\n\n"
        "_Kontaktujte nás s otázkami o vzdelávacej platforme, "
        "technickými problémami alebo predplatným._\n\n"
        "⚠️ _Neposkytujeme personalizované finančné poradenstvo._",
        parse_mode="Markdown",
    )


async def tip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global _tip_index
    t = TIPS[_tip_index % len(TIPS)]
    _tip_index += 1
    await update.message.reply_text(
        f"💡 *Vzdelávací tip dňa:*\n\n{t}"
        + DISCLAIMER,
        parse_mode="Markdown",
    )


# ── Keyword-based smart responses ─────────────────────────────────────────────

KEYWORD_RESPONSES = {
    ("investici", "investovat", "etf", "akcie", "portfoio", "portfólio", "fond", "sporeni", "sporit"): "invest",
    ("hypoteka", "hypotéka", "uver", "úver", "banka", "splátka", "nehnutelnost", "nehnuteľnosť", "byt", "dom", "kupim"): "mortgage",
    ("poistenie", "poisťovnia", "poistit", "poistiť", "zivotne", "životné", "majetkove", "úraz"): "insurance",
    ("dan", "daň", "danove", "daňové", "odpocet", "ii. pilier", "iii. pilier", "pilier"): "tax",
    ("nbs", "skúška", "skuska", "licencia", "186/2009", "sprostredkovatel"): "nbs",
    ("ahoj", "zdravim", "dobrý", "dobry", "cau", "hello", "hi"): "greeting",
    ("pomoc", "pomoct", "co robite", "čo robíte", "sluzby", "služby", "ponuka"): "help_info",
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
            "🛡️ *Vzdelávanie — Poistenie*\n\n"
            "*Druhy poistenia:*\n"
            "• Životné — ochrana rodiny pri úmrtí alebo invalidite\n"
            "• Majetkové — byt, dom, auto (havarijné, PZP)\n"
            "• Zodpovednostné — škody spôsobené tretím osobám\n\n"
            "*Na čo sa zamerať pri výbere:*\n"
            "• Poistná suma — musí pokryť reálne riziko\n"
            "• Výluky z poistenia — čítajte dôkladne\n"
            "• Poistné plnenie — ako rýchlo a za akých podmienok\n\n"
            "_Naučte sa viac o typoch poistenia na finadvisor.sk/learn_"
            + DISCLAIMER
            + SITE_CTA,
            parse_mode="Markdown",
        )
    elif matched_type == "tax":
        await update.message.reply_text(
            "💰 *Vzdelávanie — Dane & Penzie*\n\n"
            "*Daňový systém SR — základy:*\n"
            "• Sadzba 19% — príjmy do €41 445/rok\n"
            "• Sadzba 25% — príjmy nad túto hranicu\n"
            "• Nezdaniteľná časť základu dane: ~€4 716/rok (2025)\n\n"
            "*II. pilier — čo vedieť:*\n"
            "Povinné od roku 2005. Výber fondu závisí od veku. "
            "Indexové fondy majú historicky lepší výnos.\n\n"
            "*III. pilier — bonus od štátu:*\n"
            "Príspevok štátu + daňový odpočet až €180/rok pri vklade €25+/mes.\n\n"
            "_Daňová vzdelávacia kalkulačka: finadvisor.sk/app_"
            + DISCLAIMER
            + SITE_CTA,
            parse_mode="Markdown",
        )
    elif matched_type == "nbs":
        await cmd_nbs(update, ctx)
    elif matched_type == "greeting":
        await start(update, ctx)
    elif matched_type == "help_info":
        await help_cmd(update, ctx)
    else:
        await update.message.reply_text(
            "Ďakujem za správu! 🙏\n\n"
            "Mám vzdelávacie materiály na tieto témy:\n"
            "📈 /vzdelavanie — Investície, hypotéky, dane\n"
            "🔢 /kalkulacky — Orientačné kalkulačky\n"
            "📚 /nbs — Príprava na skúšku NBS\n"
            "💡 /tip — Vzdelávací tip dňa\n"
            "📞 /kontakt — Kontakt\n\n"
            "⚠️ _Všetok obsah je vzdelávací, nie finančné poradenstvo._"
            + SITE_CTA,
            parse_mode="Markdown",
        )


# ── Conversation: Financial IQ Dotazník ───────────────────────────────────────

async def analyze_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "📊 *Finančný IQ Dotazník*\n\n"
        "Odpovedzte na niekoľko otázok a zistíte svoj orientačný finančný profil.\n\n"
        "⚠️ _Výsledok je informatívny a neslúži ako finančné odporúčanie._\n\n"
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
    await update.message.reply_text(
        "📱 Telefón? _(napr. +421 900 000 000)_ alebo napíšte _preskocit_",
        parse_mode="Markdown",
    )
    return ASK_PHONE


async def got_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    ctx.user_data["phone"] = "" if val.lower() == "preskocit" else val
    await update.message.reply_text(
        "💰 Mesačný príjem (€)? Napíšte číslo, napr. _2500_",
        parse_mode="Markdown",
    )
    return ASK_INCOME


async def got_income(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["monthly_income"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte číslo, napr. 2500")
        return ASK_INCOME
    await update.message.reply_text("💳 Mesačné výdavky (€)?")
    return ASK_EXPENSES


async def got_expenses(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["monthly_expenses"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte číslo, napr. 1500")
        return ASK_EXPENSES
    await update.message.reply_text(
        "🏦 Celkové úspory (€)? _(napíšte 0 ak nemáte)_",
        parse_mode="Markdown",
    )
    return ASK_SAVINGS


async def got_savings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["total_savings"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte číslo, napr. 5000")
        return ASK_SAVINGS
    await update.message.reply_text(
        "💳 Celkový dlh (€)? _(úvery, hypotéka atď. — napíšte 0 ak nemáte)_",
        parse_mode="Markdown",
    )
    return ASK_DEBT


async def got_debt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["total_debt"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Zadajte číslo")
        return ASK_DEBT
    await update.message.reply_text("Koľko máte rokov?")
    return ASK_AGE


async def got_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["age"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Zadajte celé číslo, napr. 32")
        return ASK_AGE
    keyboard = [["0 rokov", "1-3 roky"], ["4+ rokov"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "📈 Skúsenosti s investovaním?",
        reply_markup=markup,
    )
    return ASK_EXPERIENCE


async def got_experience(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {"0 rokov": 0, "1-3 roky": 2, "4+ rokov": 5}
    ctx.user_data["investment_experience"] = mapping.get(update.message.text, 0)
    keyboard = [["Krátkodobý (< 2r)", "Strednodobý (2-5r)"], ["Dlhodobý (5r+)"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Investičný horizont?", reply_markup=markup)
    return ASK_HORIZON


async def got_horizon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {
        "Krátkodobý (< 2r)": "short",
        "Strednodobý (2-5r)": "medium",
        "Dlhodobý (5r+)": "long",
    }
    ctx.user_data["investment_horizon"] = mapping.get(update.message.text, "medium")
    keyboard = [["Sporenie", "Dôchodok"], ["Nehnuteľnosť", "Vzdelanie"], ["Rast"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Váš hlavný finančný cieľ?", reply_markup=markup)
    return ASK_GOAL


async def got_goal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mapping = {
        "Sporenie": "savings", "Dôchodok": "retirement",
        "Nehnuteľnosť": "property", "Vzdelanie": "education", "Rast": "growth",
    }
    ctx.user_data["goal_type"] = mapping.get(update.message.text, "savings")

    # Uloženie záujemcu do systému (bez finančných údajov)
    lead_data = {
        "full_name": ctx.user_data.get("full_name", ""),
        "email": ctx.user_data.get("email", ""),
        "phone": ctx.user_data.get("phone", ""),
        "interest": ctx.user_data.get("goal_type", "education"),
        "message": "Telegram IQ dotazník — záujemca o vzdelávanie",
        "source": "telegram",
    }
    api_post("/leads", lead_data)

    age = ctx.user_data.get("age", 40)
    cashflow = ctx.user_data.get("monthly_income", 0) - ctx.user_data.get("monthly_expenses", 0)
    exp = ctx.user_data.get("investment_experience", 0)
    horizon = ctx.user_data.get("investment_horizon", "medium")

    # IQ skóre — informatívne, nie odporúčanie
    score = 0
    score += 25 if age < 35 else (15 if age <= 50 else 5)
    score += 25 if cashflow > 1000 else (15 if cashflow >= 500 else 5)
    score += 25 if exp >= 4 else (15 if exp >= 1 else 5)
    score += 25 if horizon == "long" else (15 if horizon == "medium" else 5)

    if score >= 70:
        profile = "Dynamický"
        edu_hint = (
            "Na platforme nájdete vzdelávacie materiály o ETF fondoch, "
            "akciových trhoch a dlhodobom investovaní."
        )
    elif score >= 40:
        profile = "Vyvážený"
        edu_hint = (
            "Na platforme nájdete materiály o kombinácii rastových a konzervatívnych "
            "nástrojov, II. pilieri a pravidelnom sporení."
        )
    else:
        profile = "Konzervatívny"
        edu_hint = (
            "Na platforme nájdete materiály o III. pilieri, "
            "termínovaných vkladoch a bezpečnom sporení."
        )

    await update.message.reply_text(
        f"✅ *Finančný IQ dotazník dokončený!*\n\n"
        f"Váš orientačný profil: *{profile}* (skóre: {score}/100)\n\n"
        f"📚 *Vzdelávacie zdroje pre váš profil:*\n{edu_hint}\n\n"
        f"🎓 Preskúmajte naše vzdelávacie materiály na *finadvisor.sk/learn*\n\n"
        f"⚠️ _Toto je orientačný výsledok na vzdelávacie účely. "
        f"Pre personalizované finančné plánovanie kontaktujte licencovaného "
        f"finančného poradcu registrovaného v NBS._",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Dotazník zrušený. Môžete začať znova cez /analyze",
        reply_markup=get_main_keyboard(),
    )
    return ConversationHandler.END


async def menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    text_lower = text.lower()

    # ── Daily challenge answer ──────────────────────────────
    if ctx.user_data.get("awaiting_daily"):
        answer = text.strip().upper()
        ch = ctx.user_data.get("daily_challenge", {})
        if answer in ("A", "B", "C", "D"):
            uid = update.effective_user.id
            correct = ch.get("ans", "")
            xp_reward = ch.get("xp", 25)
            ctx.user_data["awaiting_daily"] = False
            ctx.user_data["daily_date"] = _today()
            # streak
            last_d = ctx.user_data.get("last_day")
            today = _today()
            yesterday = (_dt.date.today() - _dt.timedelta(days=1)).isoformat()
            if last_d == yesterday:
                ctx.user_data["streak"] = ctx.user_data.get("streak", 0) + 1
            elif last_d != today:
                ctx.user_data["streak"] = 1
            ctx.user_data["last_day"] = today
            streak = ctx.user_data.get("streak", 1)

            if answer == correct:
                new_xp = _add_xp(uid, xp_reward)
                lvl = _level_name(new_xp)
                await update.message.reply_text(
                    f"🎉 *Správne! +{xp_reward} XP*\n\n"
                    f"⚡ Celkom: *{new_xp} XP* | {lvl}\n"
                    f"🔥 Streak: *{streak} dní*\n\n"
                    f"{'🏆 Level up!' if new_xp in [100,300,600,1000,1500,2200,3000] else '📈 Skvelá práca!'}\n\n"
                    f"📚 Pokračuj: https://finadvisor.sk/learn\n"
                    f"/leaderboard — porovnaj sa s ostatnými",
                    parse_mode="Markdown"
                )
            else:
                new_xp = _add_xp(uid, 5)
                await update.message.reply_text(
                    f"❌ Nesprávne. Správna odpoveď: *{correct}*\n\n"
                    f"+5 XP za účasť 💪\n"
                    f"⚡ Celkom: *{new_xp} XP*\n\n"
                    f"Nauč sa viac: https://finadvisor.sk/learn\n"
                    f"Skús zajtra: /vyzva",
                    parse_mode="Markdown"
                )
            return

    if "finančný iq" in text_lower or "analyza" in text_lower or "iq test" in text_lower:
        return await analyze_start(update, ctx)
    elif "výzva" in text_lower or "vyzva" in text_lower or "🎯" in text:
        await cmd_daily_challenge(update, ctx)
    elif "skóre" in text_lower or "skore" in text_lower or "xp" in text_lower:
        await cmd_score(update, ctx)
    elif "tip" in text_lower:
        await tip(update, ctx)
    elif "kontakt" in text_lower:
        await contact(update, ctx)
    elif "pomoc" in text_lower or "help" in text_lower:
        await help_cmd(update, ctx)
    elif "vzdelávanie" in text_lower or "vzdelavanie" in text_lower:
        await cmd_vzdelavanie(update, ctx)
    elif "nbs" in text_lower or "príprava" in text_lower:
        await cmd_nbs(update, ctx)
    else:
        await smart_response(update, ctx)


async def cmd_test(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Cvičná NBS otázka zo zverejnených materiálov."""
    sector = None
    if ctx.args:
        sector = " ".join(ctx.args)

    path = "/quiz/question/random"
    if sector:
        path += "?sector=" + urllib.parse.quote(sector)

    data = api_get(path)
    if not data:
        await update.message.reply_text(
            "Nepodarilo sa načítať otázku. Skúste neskôr alebo navštívte finadvisor.sk/learn"
        )
        return

    opts = data.get("options", {})
    opts_lines = "\n".join(f"  {k}. {v}" for k, v in sorted(opts.items()))
    correct = data.get("correct", "?").upper()
    msg = (
        f"📝 *Cvičná otázka č. {data['number']}*\n"
        f"Sekcia: {data['section']}\n\n"
        f"{data['text']}\n\n"
        f"{opts_lines}\n\n"
        f"✅ Správna odpoveď: [ {correct} ]\n\n"
        f"_Otázky sú zo zverejnených materiálov NBS pre vzdelávacie účely._\n"
        f"Ďalšia otázka: /test"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


# ══════════════════════════════════════════════════════════════
# GAMIFICATION — Daily Challenge · Score · Leaderboard
# ══════════════════════════════════════════════════════════════

DAILY_TG = [
    {"q": "Čo je ETF fond?", "opts": ["A) Termínovaný vklad", "B) Fond obchodovaný na burze", "C) Typ hypotéky", "D) Bankový produkt"], "ans": "B", "xp": 25},
    {"q": "Max. daňový odpočet III. pilier / rok?", "opts": ["A) €100", "B) €180", "C) €250", "D) €500"], "ans": "B", "xp": 25},
    {"q": "Čo je RPMN pri hypotéke?", "opts": ["A) Ročná percentuálna miera nákladov", "B) Regulačné percento miesta nákladov", "C) Reálna platba mesačná norma", "D) Rozšírená platba mesačnej normy"], "ans": "A", "xp": 30},
    {"q": "Koľko pilierov má dôchodkový systém SR?", "opts": ["A) 1", "B) 2", "C) 3", "D) 4"], "ans": "C", "xp": 20},
    {"q": "Čo je to diverzifikácia portfólia?", "opts": ["A) Predaj všetkých akcií", "B) Len zlato", "C) Rozloženie investícií do viacerých aktív", "D) Jeden fond"], "ans": "C", "xp": 25},
    {"q": "Inflačný cieľ ECB je?", "opts": ["A) 0%", "B) 1%", "C) 2%", "D) 5%"], "ans": "C", "xp": 30},
    {"q": "P/E ratio akcie znamená?", "opts": ["A) Pomer ceny k zisku", "B) Poistná expozícia", "C) Preferenčné euro", "D) Pomer príjmu k výdavkom"], "ans": "A", "xp": 35},
]

# Simple in-memory XP store (resets on restart — for persistent use DB)
_tg_xp: dict[int, int] = {}
_tg_streak: dict[int, str] = {}

import datetime as _dt

def _today() -> str:
    return _dt.date.today().isoformat()

def _get_xp(uid: int) -> int:
    return _tg_xp.get(uid, 0)

def _add_xp(uid: int, amount: int) -> int:
    _tg_xp[uid] = _tg_xp.get(uid, 0) + amount
    return _tg_xp[uid]

def _level_name(xp: int) -> str:
    levels = [(0,"🌱 Nováčik"),(100,"📚 Učeň"),(300,"🔍 Záujemca"),(600,"👀 Pozorovateľ"),
              (1000,"📊 Analytik"),(1500,"♟️ Stratég"),(2200,"🎯 Expert"),(3000,"🏆 Majster"),(4000,"🦉 Mentor"),(6000,"⚡ Legenda")]
    name = levels[0][1]
    for threshold, lname in levels:
        if xp >= threshold: name = lname
    return name


async def cmd_daily_challenge(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    today = _today()
    last = ctx.user_data.get("daily_date")
    ch = DAILY_TG[_dt.date.today().day % len(DAILY_TG)]

    if last == today:
        await update.message.reply_text(
            f"✅ *Dnešnú výzvu si už splnil!*\n\n"
            f"Tvoje XP: *{_get_xp(uid)} XP* | {_level_name(_get_xp(uid))}\n\n"
            f"Príď zajtra pre novú výzvu 🔥\n\n"
            f"📚 Pokračuj na: https://finadvisor.sk/learn",
            parse_mode="Markdown"
        )
        return

    opts_text = "\n".join(ch["opts"])
    await update.message.reply_text(
        f"🎯 *DENNÁ VÝZVA — +{ch['xp']} XP*\n\n"
        f"❓ {ch['q']}\n\n"
        f"{opts_text}\n\n"
        f"Odpovedaj písmenom: A, B, C alebo D",
        parse_mode="Markdown"
    )
    ctx.user_data["daily_challenge"] = ch
    ctx.user_data["awaiting_daily"] = True


async def cmd_score(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    xp = _get_xp(uid)
    lvl = _level_name(xp)
    streak = ctx.user_data.get("streak", 0)
    await update.message.reply_text(
        f"🎮 *Tvoje skóre*\n\n"
        f"⚡ XP: *{xp}*\n"
        f"🏅 Level: *{lvl}*\n"
        f"🔥 Streak: *{streak} dní*\n\n"
        f"Zarob viac XP na: https://finadvisor.sk/learn\n"
        f"Denná výzva: /vyzva",
        parse_mode="Markdown"
    )


async def cmd_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _tg_xp:
        await update.message.reply_text("📊 Leaderboard je zatiaľ prázdny. Buď prvý! /vyzva")
        return
    sorted_xp = sorted(_tg_xp.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    lines = [f"{medals[i]} {_level_name(xp)} — *{xp} XP*" for i, (_, xp) in enumerate(sorted_xp)]
    await update.message.reply_text(
        f"🏆 *Top hráči FinAdvisor SK*\n\n" + "\n".join(lines) +
        f"\n\nTvoje XP: *{_get_xp(update.effective_user.id)}*\n/vyzva — zarob viac!",
        parse_mode="Markdown"
    )




def _register_handlers(app):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("analyze", analyze_start),
            MessageHandler(filters.Regex("📊 Finančný IQ test"), analyze_start),
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
    app.add_handler(CommandHandler("vzdelavanie", cmd_vzdelavanie))
    app.add_handler(CommandHandler("kalkulacky", cmd_kalkulacky))
    app.add_handler(CommandHandler("nbs", cmd_nbs))
    app.add_handler(CommandHandler("investovat", cmd_investovat))
    app.add_handler(CommandHandler("hypoteka", cmd_hypoteka))
    app.add_handler(CommandHandler("kontakt", contact))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CommandHandler("vyzva", cmd_daily_challenge))
    app.add_handler(CommandHandler("skore", cmd_score))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))


async def build_application(token: str) -> Application:
    """Build and initialize app for webhook mode (used by FastAPI)."""
    app = Application.builder().token(token).build()
    _register_handlers(app)
    await app.initialize()
    await app.start()
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
