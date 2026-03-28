"""
Social Media Auto-Poster — FinAdvisor SK

Posts financial tips automatically to:
  - LinkedIn (via LinkedIn API v2)
  - Facebook Page (via Graph API)
  - Twitter/X (via Twitter API v2)

Usage:
    python marketing/social/auto_post.py --platform linkedin --post tip_of_week
    python marketing/social/auto_post.py --platform all --post tip_of_week
    python marketing/social/auto_post.py --schedule   # runs daily at 09:00

Env vars required per platform:
  LinkedIn:  LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN
  Facebook:  FB_PAGE_ACCESS_TOKEN, FB_PAGE_ID
  Twitter:   TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET
"""
import os
import random
import logging
import argparse
import json
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ── Content library ────────────────────────────────────────────────────────────
POSTS = {
    "tip_of_week": [
        """💡 Vedeli ste, že III. pilier vám prinesie €180 ročne ZADARMO od štátu?

Stačí odkladať €25/mesiac a štát pridá až 60% navyše.
To je lepší výnos ako väčšina investícií bez akéhokoľvek rizika.

📩 Chcete vedieť viac? Napíšte mi alebo navštívte finadvisor.sk

#financie #sporenie #IIIpilier #Slovensko #finančnéporadenstvo""",

        """📈 ETF vs. aktívne fondy — čo si vybrať?

Historické dáta ukazujú, že 90% aktívnych fondov dlhodobo nepredčí index.

→ MSCI World ETF: ~8% ročne za posledných 30 rokov
→ Priemerný aktívny fond: ~5% mínus poplatky

Jednoduchosť vyhráva. Investujte do indexu.

#investovanie #ETF #osobnefinancie #Slovensko""",

        """🏠 Hypotéka v 2026 — čo sledovať?

✅ Sadzby klesajú → teraz je dobrý čas refinancovať
✅ Fixácia na 5 rokov môže byť výhodnejšia ako variabilná sadzba
✅ Porovnajte aspoň 5 bánk — rozdiel môže byť €100/mesiac

Pomôžem vám nájsť najlepšiu ponuku bez poplatkov.

#hypotéka #reality #bývanie #Slovensko""",

        """🧾 Daňové tipy pre rok 2026:

1️⃣ Nezdaniteľná časť: €5 646 → ušetríte až €1 072
2️⃣ III. pilier: odpočítajte až €180 zo základu dane
3️⃣ Príspevky zamestnávateľa: nezdanené do €500/rok
4️⃣ Straty z investícií: kompenzujte so ziskami

#dane #optimalizácia #financie #Slovensko""",

        """💼 II. pilier — najčastejšia chyba Slovákov:

❌ Väčšina ľudí má peniaze v dlhopisovom fonde (0-2% výnos)
✅ Pre vek pod 40 rokov je indexový fond (6-8%) oveľa lepší

Zmena fondu je zadarmo a trvá 5 minút.
Potenciálny rozdiel za 30 rokov: desaťtisíce eur.

Chcete pomôcť s výberom? 👇

#IIpilier #dôchodok #financie #Slovensko""",
    ],

    "promo": [
        """🎯 Prvá konzultácia ZADARMO — FinAdvisor SK

Pomôžem vám s:
📈 Investíciami
🏠 Hypotékou
🏦 II/III pilierom
🛡️ Poistením
🧾 Daňami

Online aj osobne. Bez záväzkov.

👉 finadvisor.sk
📩 info@finadvisor.sk

#finančnýporadca #Slovensko #osobnefinancie""",
    ],
}


def _http_post(url: str, data: dict, headers: dict) -> dict:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {error_body}")


def post_linkedin(text: str) -> bool:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    urn = os.getenv("LINKEDIN_PERSON_URN")  # e.g. urn:li:person:ABC123
    if not token or not urn:
        logger.error("LinkedIn: missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN")
        return False

    payload = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    try:
        _http_post(
            "https://api.linkedin.com/v2/ugcPosts",
            payload,
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        logger.info("✓ LinkedIn post published")
        return True
    except Exception as e:
        logger.error("✗ LinkedIn failed: %s", e)
        return False


def post_facebook(text: str) -> bool:
    token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FB_PAGE_ID")
    if not token or not page_id:
        logger.error("Facebook: missing FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID")
        return False

    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    try:
        _http_post(url, {"message": text, "access_token": token}, {"Content-Type": "application/json"})
        logger.info("✓ Facebook post published")
        return True
    except Exception as e:
        logger.error("✗ Facebook failed: %s", e)
        return False


def post_twitter(text: str) -> bool:
    """Posts via Twitter API v2 using OAuth 1.0a."""
    import hmac
    import hashlib
    import base64
    import time
    import uuid

    api_key = os.getenv("TW_API_KEY")
    api_secret = os.getenv("TW_API_SECRET")
    access_token = os.getenv("TW_ACCESS_TOKEN")
    access_secret = os.getenv("TW_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        logger.error("Twitter: missing one or more TW_* env vars")
        return False

    # Truncate to 280 chars
    tweet_text = text[:280]

    url = "https://api.twitter.com/2/tweets"
    nonce = uuid.uuid4().hex
    ts = str(int(time.time()))

    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": ts,
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }

    param_str = "&".join(f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}"
                         for k, v in sorted(oauth_params.items()))
    base_str = f"POST&{urllib.parse.quote(url)}&{urllib.parse.quote(param_str)}"
    sign_key = f"{urllib.parse.quote(api_secret)}&{urllib.parse.quote(access_secret)}"
    signature = base64.b64encode(
        hmac.new(sign_key.encode(), base_str.encode(), hashlib.sha1).digest()
    ).decode()

    oauth_params["oauth_signature"] = signature
    auth_header = "OAuth " + ", ".join(
        f'{urllib.parse.quote(k)}="{urllib.parse.quote(v)}"'
        for k, v in sorted(oauth_params.items())
    )

    try:
        _http_post(url, {"text": tweet_text}, {
            "Authorization": auth_header,
            "Content-Type": "application/json",
        })
        logger.info("✓ Twitter post published")
        return True
    except Exception as e:
        logger.error("✗ Twitter failed: %s", e)
        return False


PLATFORM_FN = {
    "linkedin": post_linkedin,
    "facebook": post_facebook,
    "twitter": post_twitter,
}


def run(platform: str, post_key: str, dry_run: bool = False) -> None:
    pool = POSTS.get(post_key)
    if not pool:
        raise ValueError(f"Unknown post key '{post_key}'. Available: {list(POSTS.keys())}")

    text = random.choice(pool)

    if dry_run:
        logger.info("[DRY RUN] Would post to '%s':\n%s", platform, text)
        return

    platforms = list(PLATFORM_FN.keys()) if platform == "all" else [platform]
    for p in platforms:
        PLATFORM_FN[p](text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAdvisor SK — Social media auto-poster")
    parser.add_argument("--platform", default="all", help="linkedin|facebook|twitter|all")
    parser.add_argument("--post", default="tip_of_week", help="tip_of_week|promo")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.platform, args.post, args.dry_run)
