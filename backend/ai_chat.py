"""
FinAdvisor AI Chat — Smart Financial Assistant
POST /ai/chat  { "message": "...", "history": [] }
Uses OpenAI GPT when OPENAI_API_KEY is set, otherwise smart rule-based responses.
"""
import os, re
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["ai"])

SYSTEM_PROMPT_SK = """Si FinAdvisor AI — odborný finančný vzdelávací asistent pre slovenský trh.
Pravidlá:
- Odpovedáš na otázky o osobných financiách, investíciách, bankách, daniach, hypotékach, poistení, NBS, kryptomenách.
- Odpovedáš vždy v slovenčine, stručne a konkrétne.
- Na konci každej odpovede napíš: ⚠️ Toto je vzdelávacia informácia, nie licencované finančné poradenstvo.
- Ak otázka nie je o financiách, zdvorilo odmietnuš."""

SYSTEM_PROMPT_UK = """Ти FinAdvisor AI — фінансовий освітній асистент для словацького ринку.
Правила:
- Відповідаєш на питання про особисті фінанси, інвестиції, банки, податки, іпотеки, страхування, NBS, криптовалюти.
- Відповідаєш ЗАВЖДИ українською мовою, стисло і конкретно.
- В кінці кожної відповіді напиши: ⚠️ Це освітня інформація, а не ліцензована фінансова порада.
- Якщо питання не стосується фінансів, ввічливо відмов."""

SYSTEM_PROMPT = SYSTEM_PROMPT_SK

# ─── KNOWLEDGE BASE ────────────────────────────────────────────────────────────
KB = [
  # ETF & investície
  (r"etf|index.?fond|pasív|vwce|cspx|msci|s.p.500|dca|dollar.cost",
   """**ETF (Exchange-Traded Fund)** je pasívny fond kopírujúci trhový index, obchodovaný na burze ako akcia.

**Pre slovenských investorov odporúčané UCITS ETF:**
- 🌍 **VWCE** — Vanguard FTSE All-World (celý svet, TER 0.22%)
- 🇺🇸 **CSPX** — iShares Core S&P 500 (USA, TER 0.07%, domicil Írsko)
- 🇪🇺 **MEUD** — STOXX Europe 600 (Európa, TER 0.07%)

**Stratégia DCA** = každý mesiac investuješ fixnú sumu bez ohľadu na cenu → priemernuješ nákupnú cenu.

**Brokeri dostupní pre SR:** DEGIRO, IBKR, XTB, Finax

**Daňovanie:** výnosy z ETF predaja zdanené 19% (príjem do 41 445€/rok) alebo 25% nad tento limit."""),

  # Hypotéka
  (r"hypotéka|hypoteka|úver na byt|mortgage|fixácia|dsti|lti|úrokové sadzb|splátk",
   """**Hypotéka na Slovensku 2024/2025:**

**Podmienky bánk:**
- **DTI** (Debt-to-Income): celkové dlhy max 8× ročný príjem
- **DSTI**: mesačné splátky max 40% čistého príjmu
- **LTV**: zvyčajne do 80% hodnoty nehnuteľnosti

**Fixácia úrokovej sadzby:**
- 3-ročná: ~3.8-4.2% p.a.
- 5-ročná: ~3.5-4.0% p.a.
- 10-ročná: ~4.0-4.5% p.a.

**Štátny príspevok pre mladých** (do 35 rokov): 3% z výšky úveru, max 70 000€

**Postup:** banková ponuka → znalecký posudok → zmluva o úvere → čerpanie

💡 Vždy porovnaj **RPSN** (nie len úrok) a predčasné splatenie."""),

  # Dôchodok & sporenie
  (r"dôchodok|dochodok|iii.?pilier|3.?pilier|dds|doplnkové|penzia|penz|retire",
   """**Dôchodkové sporenie v SR:**

**I. pilier** — Sociálna poisťovňa (povinný, 18% mzdy)
**II. pilier** — DSS (dobrovoľný od 35r., 4% mzdy) — odporúčam vstúpiť!
**III. pilier** — DDS (dobrovoľný, daňový odpočet)

**III. pilier — výhody:**
- Príspevok zamestnávateľa (nezdanený benefit)
- Daňový odpočet: **až 180€/rok** (úspora 34.20€ na daniach)
- Štátny príspevok: až 90€/rok (pri vklade 25€/mesiac)

**Odporúčaná stratégia:**
1. Vstúp do II. piliera (ak si do 35r.)
2. Sporenie v III. pilieri min. 25€/mes
3. Zvyšok do ETF cez brokera

**Pravidlo 4%:** kapitál = želaný ročný príjem / 4%
→ Chceš 1000€/mes v dôchodku? Potrebuješ 300 000€ kapitálu."""),

  # Dane
  (r"daň|dan\b|daňov|dpfo|dph|odpočet|daňové priznan|19%|25%|zdaneni",
   """**Daňový systém SR 2025:**

**Daň z príjmu FO:**
- Do 41 445.46€/rok → **19%**
- Nad 41 445.46€/rok → **25%** (z časti nad limit)
- NČZD (nezdaniteľná časť): 5 646.48€/rok

**Daňový bonus na deti:**
- Dieťa do 15r.: 140€/mesiac
- Dieťa 15-25r.: 50€/mesiac

**Investície:**
- Výnosy z predaja akcií/ETF: **19%** alebo 25%
- Dividendy: **zrážková daň 7%**
- Crypto: príjem z predaja = zdaniteľný príjem

**Odpočty od základu dane:**
- III. pilier: max 180€/rok
- Hypotéka (úroky): max 400€/rok (pre mladých do 35r.)
- Životné poistenie: max 180€/rok"""),

  # Rozpočet
  (r"rozpočet|budzet|budget|úspor|spori|výdavk|príjm|cash.?flow|50.30.20",
   """**Osobný rozpočet — metóda 50/30/20:**

- **50%** príjmu → Potreby (nájom, jedlo, energie, splátky)
- **30%** príjmu → Záľuby (reštaurácie, hobby, cestovanie)
- **20%** príjmu → Sporenie & investície

**Fond núdzových situácií:**
Cieľ: 3-6 mesačných výdavkov na likvidnom účte
→ Sporiaci účet (napr. Tatra banka, VÚB, Prima banka)
→ NIE investície — musí byť okamžite dostupné

**Zlaté pravidlá:**
1. Plať najprv sebe (odložíš deň výplaty)
2. Automatizuj prevody na sporiaci účet
3. Sleduj výdavky (Spendee, Wallet, Money Manager)
4. Revízia raz za mesiac"""),

  # Akcie & dividendy
  (r"akci|dividend|stock|p/e|p.e ratio|yield|warren|blue.?chip|dow|nasdaq",
   """**Investovanie do akcií:**

**Kľúčové ukazovatele:**
- **P/E ratio** = cena akcie / zisk na akciu (historicky 15-20 pre S&P 500)
- **Dividend Yield** = ročná dividenda / cena akcie × 100
- **Payout Ratio** = % zisku vyplatená ako dividenda

**Dividendové aristokraty** = spoločnosti zvyšujúce dividendy 25+ rokov (napr. Coca-Cola, Johnson & Johnson, Procter & Gamble)

**DRIP** (Dividend Reinvestment Plan) = automatické reinvestovanie dividend → zložené úroky

**Pre začiatočníkov:**
→ Začni s ETF (diverzifikácia), nie jednotlivými akciami
→ Jednotlivé akcie max 5-10% portfólia"""),

  # NBS skúška
  (r"nbs|186.?2009|sprostredkovateľ|skúšk|skuška|sektor.?a|sektor.?b|fia|oba|mifid",
   """**NBS — Národná banka Slovenska:**

**Zákon č. 186/2009 Z.z.** o finančnom sprostredkovaní a poradenstve

**Sektory finančného sprostredkovania:**
- Sektor **poistenia** (A)
- Sektor **kapitálového trhu** (B)
- Sektor **doplnkového dôchodkového sporenia** (C)
- Sektor **prijímania vkladov** (D)
- Sektor **poskytovania úverov** (E)

**Skúška NBS:**
- 25 otázok z databázy ~1334 otázok
- Potrebujete min. 65% (17/25 správnych)
- Platnosť: trvalá (bez obnovy)
- Registrácia cez: nbs.sk/register

**Povinnosti FP:** odborná starostlivosť, informačná povinnosť, register NBS"""),

  # Krypto
  (r"bitcoin|btc|ethereum|eth|crypto|krypto|blockchain|defi|nft|mica|stablecoin|altcoin",
   """**Kryptomeny — základy:**

**Bitcoin (BTC):**
- Max. zásoba: 21 mil. BTC
- Halving každé ~4 roky (ďalší: 2028)
- Proof of Work konsenzus

**Ethereum (ETH):**
- Smart contracts platforma
- Proof of Stake od 2022
- DeFi a NFT ekosystém

**MiCA regulácia** (EÚ, od 2024):
- Povinné licencie pre krypto burzy
- Stablecoiny pod dohľadom EBA
- Reportovanie transakcií nad 1 000€

**Riziká:**
- Volatilita (BTC padol -80% viackrát)
- Regulačné riziko
- Bezpečnosť (hack, strata seed phrase)

**Odporúčanie:** max 5-10% portfólia, len suma ktorú môžeš stratiť"""),

  # II. pilier
  (r"ii.?pilier|2.?pilier|dss|důchodková správcovsk|starobné|sporenie|odchod do",
   """**II. pilier — Dôchodkové sporenie:**

**Ako funguje:**
- 4% z hrubej mzdy ide na osobný účet v DSS
- Štát prispieva ďalej cez Sociálnu poisťovňu

**Vstup:**
- Automaticky pri prvom zamestnaní (ak si do 35r.)
- Dobrovoľne kedykoľvek
- Do 35 rokov — **ODPORÚČAM vstúpiť!**

**DSS na Slovensku:** NN, Allianz, Uniqa, KOOPERATIVA

**Výber fondu:**
- Mladí (do 45r.) → rastový/akciový fond
- Starší → vyvážený alebo dlhopisový

**Výplata:** od dôchodkového veku (62-65r.)
- Programový výber
- Doživotný dôchodok (anuitná poisťovňa)"""),

  # Poistenie
  (r"poisteni|poistka|životn|úrazov|PZP|havarijné|zdravotn|poistné",
   """**Základné typy poistenia v SR:**

**Povinné:**
- **PZP** — povinné zmluvné poistenie auta
- Zdravotné poistenie (VšZP, Dôvera, Union)

**Odporúčané:**
- **Životné poistenie** — pri hypotéke povinné, inak ak máš závislé osoby
- **Úrazové poistenie** — ochrana príjmu pri pracovnej neschopnosti
- **Majetkové** — domácnosť, nehnuteľnosť
- **Cestovné** — pri každom výjazde do zahraničia

**Zlaté pravidlá:**
1. Poisťuj len riziká, ktoré nedokážeš sám pokryť
2. Porovnaj ceny (porovnaj.sk, bezrealitky.sk)
3. Čítaj výluky v poistnej zmluve
4. ELDP (evidenčný list dôchodkového poistenia) — sleduj raz ročne"""),

  # Banky & sporenie
  (r"banka|sporiac|vklad|úrok|dgs|100.000|účet|deposit|savings",
   """**Bankový systém SR:**

**Ochrannú vkladov (DGS):**
- Garantované vklady do **100 000€** na banku
- Fond ochrany vkladov SR
- Výplata do 7 pracovných dní

**Sporiace produkty:**
- **Bežný účet:** 0-0.5% úrok
- **Sporiaci účet:** 2-3.5% úrok (Tatra, ČSOB, Prima)
- **Termínovaný vklad:** 3-4% na 1-2 roky (nízka likvidita)
- **Štátne dlhopisy** (MF SR): 3.5-4.5% p.a.

**Stratégia pre hotovosť:**
1. Fond núdzovky → sporiaci účet (3-6 mes. výdavkov)
2. Krátkodobé ciele (1-3r.) → termínovaný vklad
3. Dlhodobé (5+r.) → ETF"""),

  # Nehnuteľnosti & REITs
  (r"reit|nehnuteľnosť|nehnutelnost|prenájom|nájom|real estate|byt na investíci",
   """**Investovanie do nehnuteľností:**

**Priama investícia:**
- Výhody: hmatateľné aktívum, ochrana pred infláciou
- Nevýhody: nízka likvidita, správa, vysoký vstupný kapitál
- Výnosnosť prenájmu v SR: 3-5% ročne (Bratislava ~3%)

**REITs (Real Estate Investment Trusts):**
- Fondy investujúce do nehnuteľností
- Obchodované na burze ako akcia
- Min. 90% zisku vyplatí ako dividendu
- Odporúčané: **VNQ** (US REITs), **IWDP** (Global REITs)
- TER ~0.12-0.22%

**Výhody REITs vs. priama investícia:**
✅ Likvidita (predáš kedy chceš)
✅ Diverzifikácia (stovky budov)
✅ Nízky vstupný kapitál (od 50€)
✅ Žiadna správa"""),

  # Finančná sloboda & FIRE
  (r"finančná sloboda|fire movement|passiv.?príjem|pasívny príjem|4% pravidl|portfólio",
   """**FIRE Movement (Financial Independence, Retire Early):**

**4% pravidlo:**
- Výber 4% portfólia ročne je dlhodobo udržateľný
- Výpočet: Ročné výdavky × 25 = potrebný kapitál
- Príklad: 1500€/mes → 1500×12×25 = **450 000€**

**FIRE varianty:**
- **Lean FIRE:** minimálny životný štýl (<1500€/mes)
- **Fat FIRE:** komfortný životný štýl (>3000€/mes)
- **Barista FIRE:** čiastočná práca + investície

**Cesta k FIRE:**
1. Miera úspor > 50% príjmu
2. Investuj do low-cost ETF (VWCE)
3. Minimalizuj dane (III. pilier, daňové odpočty)
4. Zvyšuj príjem (kariéra, freelance)

**Slovenská realita:**
Pri priemernej mzde 1400€ netto a úsporách 40% → FIRE za ~20 rokov"""),
]

def smart_reply(message: str) -> str:
    msg = message.lower()
    for pattern, response in KB:
        if re.search(pattern, msg):
            return response + "\n\n⚠️ *Toto je vzdelávacia informácia, nie licencované finančné poradenstvo podľa §1 ods. 2 zákona č. 186/2009 Z.z.*"
    
    # Generic financial response
    return """Zaujímavá otázka! Tu je niekoľko základných finančných princípov, ktoré sa vzťahujú na väčšinu situácií:

**Základné pravidlá zdravých financií:**
1. 💰 Sporenie: aspoň 20% príjmu mesačne
2. 🛡️ Fond núdzovky: 3-6 mesačných výdavkov
3. 📈 Investície: ETF (VWCE, CSPX) pre dlhodobý rast
4. 🏦 Dlhy: splácaj od najvyššieho úroku
5. 🎓 Vzdelávanie: každý mesiac 1 kurz alebo kniha

Pre konkrétnejšiu odpoveď skúste sa opýtať na:
- ETF a investovanie
- Hypotéky a úvery  
- Dôchodkové sporenie (II. a III. pilier)
- Dane a daňové optimalizácie
- Osobný rozpočet a sporenie

⚠️ *Toto je vzdelávacia informácia, nie licencované finančné poradenstvo podľa §1 ods. 2 zákona č. 186/2009 Z.z.*"""


class ChatRequest(BaseModel):
    message: str
    history: list = []
    lang: str = "sk"

class ChatResponse(BaseModel):
    reply: str
    model: str


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    system_prompt = SYSTEM_PROMPT_UK if req.lang == "uk" else SYSTEM_PROMPT_SK

    # Use OpenAI if key is available
    if api_key and api_key.startswith("sk-"):
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            messages = [{"role": "system", "content": system_prompt}]
            for h in req.history[-6:]:
                if h.get("role") in ("user", "assistant") and h.get("content"):
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": req.message})
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=600,
                temperature=0.7,
            )
            return ChatResponse(reply=response.choices[0].message.content, model="gpt-3.5-turbo")
        except Exception:
            pass  # fallback to smart replies

    # Smart knowledge-base reply
    reply = smart_reply(req.message)
    return ChatResponse(reply=reply, model="finadvisor-kb-v1")
