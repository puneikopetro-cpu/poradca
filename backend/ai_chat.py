"""
AI Chat endpoint — OpenAI GPT-3.5-turbo
POST /ai/chat  { "message": "..." }  → { "reply": "..." }
Fallback to smart keyword responses if no API key set.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["ai"])

SYSTEM_PROMPT = """Si FinAdvisor AI — inteligentný finančný vzdelávací asistent pre slovenský trh.

Tvoje pravidlá:
1. Odpovedáš VÝLUČNE na otázky o osobných financiách, investíciách, bankách, daniach, hypotékach, poistení, dôchodkovom sporení, NBS regulácii, kryptomenách a finančnom plánovaní.
2. Každú odpoveď zakončíš: "⚠️ Toto je vzdelávacia informácia, nie licencované finančné poradenstvo."
3. Odpovedáš stručne, konkrétne a v slovenčine.
4. Pri otázkach o slovenských špecifikách (II. pilier, III. pilier, NBS, daňový bonus) uvádzaš aktuálne platné informácie pre SR.
5. Ak sa ťa spýtajú na niečo mimo financií, zdvorilo odmietnuš a nasmeruješ na finančnú tému.

Štýl: odborný ale priateľský, ako dobrý priateľ — finančný expert."""

FALLBACK = {
    "etf":      "ETF (Exchange-Traded Fund) je pasívny fond obchodovaný na burze. Pre slovenských investorov sú ideálne UCITS ETF domicilované v Írsku: **CSPX** (S&P 500, TER 0.07%), **VWCE** (celosvetový, TER 0.22%). Investujte pravidelne — DCA stratégia. ⚠️ Vzdelávacia info, nie poradenstvo.",
    "hypoteka": "Hypotéka v SR: banky hodnotia DTI (max 8× ročný príjem) a DSTI (max 40% splátky/príjem). Fixácia 3/5/10 rokov. Pre mladých do 35r.: štátny príspevok 3%. Vždy porovnajte RPSN, nie len úrok. ⚠️ Vzdelávacia info.",
    "nbs":      "NBS skúška: 5 sektorov (poistenie, DDS, investície, úvery, kapitálový trh). 25 otázok, potrebujete 65%. V kurze 'Príprava na skúšku NBS' máte 1 334 cvičných otázok z reálnej databázy. ⚠️ Vzdelávacia info.",
    "daň":      "Zdaňovanie investícií v SR: výnosy z predaja akcií/ETF zdanené 19% (príjem do 41 445€/rok) alebo 25% (nad). III. pilier: daňový odpočet až 180€/rok. Dividendy: zrážková daň 7%. ⚠️ Vzdelávacia info.",
    "default":  "Skvelá otázka! Pre presnú odpoveď aktivujte AI (potrebný OpenAI kľúč). Medzitým si prezrite naše kurzy — každý obsahuje detailné vzdelávacie materiály práve pre túto tému. ⚠️ Vzdelávacia info.",
}


class ChatRequest(BaseModel):
    message: str
    history: list = []


class ChatResponse(BaseModel):
    reply: str
    model: str


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key or api_key == "your-key-here":
        # Smart keyword fallback
        msg = req.message.lower()
        if any(w in msg for w in ["etf","fond","cspx","vwce","index"]):
            return ChatResponse(reply=FALLBACK["etf"], model="fallback")
        if any(w in msg for w in ["hypotéka","hypoteka","úver","banka","dsti"]):
            return ChatResponse(reply=FALLBACK["hypoteka"], model="fallback")
        if any(w in msg for w in ["nbs","skúška","skuska","sprostredkovateľ","186/2009"]):
            return ChatResponse(reply=FALLBACK["nbs"], model="fallback")
        if any(w in msg for w in ["daň","dan","19%","25%","odpočet","iii pilier","3. pilier"]):
            return ChatResponse(reply=FALLBACK["daň"], model="fallback")
        return ChatResponse(reply=FALLBACK["default"], model="fallback")

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Add last 6 messages of history for context
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
        reply = response.choices[0].message.content
        return ChatResponse(reply=reply, model="gpt-3.5-turbo")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)[:200]}")
