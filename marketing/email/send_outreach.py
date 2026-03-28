"""
Email Outreach Automation — FinAdvisor SK

Sends personalized cold outreach emails to potential clients.
Uses Gmail SMTP (App Password) or any SMTP server.

Usage:
    python marketing/email/send_outreach.py --list leads.csv --template welcome
    python marketing/email/send_outreach.py --list leads.csv --template followup

CSV format: email,full_name,interest,company(optional)

Templates available: welcome, followup, newsletter
"""
import argparse
import csv
import smtplib
import time
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Config (set via env vars or .env) ─────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")           # your Gmail
SMTP_PASS = os.getenv("SMTP_PASS", "")           # Gmail App Password
FROM_NAME = os.getenv("FROM_NAME", "FinAdvisor SK")
FROM_EMAIL = os.getenv("SMTP_USER", "info@finadvisor.sk")
DELAY_BETWEEN_EMAILS = float(os.getenv("EMAIL_DELAY_SEC", "3"))  # avoid spam filters


# ── Email templates ────────────────────────────────────────────────────────────
TEMPLATES = {
    "welcome": {
        "subject": "Bezplatná finančná analýza pre vás, {first_name}",
        "html": """
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333">
  <h2 style="color:#1d4ed8">Ahoj {first_name} 👋</h2>
  <p>Som finančný poradca pôsobiaci na Slovensku a rád by som vám ponúkol <strong>bezplatnú 15-minútovú finančnú analýzu</strong>.</p>
  <p>Pomáham klientom s:</p>
  <ul>
    <li>📈 Investíciami (ETF, MSCI World, II. pilier)</li>
    <li>🏠 Hypotékami — porovnám všetky banky za vás</li>
    <li>🏦 III. pilier — štátna prémia až €180/rok</li>
    <li>🧾 Daňovou optimalizáciou</li>
  </ul>
  <p>Neúčtujem poplatky za poradenstvo — zarábam z provízií od bánk a poisťovní.</p>
  <p style="margin-top:24px">
    <a href="https://finadvisor.sk/#kontakt" style="background:#1d4ed8;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">
      Objednať bezplatnú konzultáciu →
    </a>
  </p>
  <p style="margin-top:32px;color:#999;font-size:12px">
    Ak nemáte záujem, jednoducho odpovedzte "unsubscribe" a viac vám nepíšem.<br/>
    FinAdvisor SK · NBS licencia
  </p>
</body></html>
""",
    },
    "followup": {
        "subject": "Ešte jedna vec, {first_name}",
        "html": """
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333">
  <h2 style="color:#1d4ed8">Ahoj {first_name},</h2>
  <p>Pred pár dňami som vám písal ohľadom bezplatnej finančnej analýzy.</p>
  <p>Chcel som sa len opýtať — máte teraz 15 minút na krátky hovor? Môžeme to urobiť online (Google Meet / Teams).</p>
  <p>Mnoho klientov po prvej konzultácii ušetrilo stovky eur ročne len optimalizáciou II. a III. piliera.</p>
  <p style="margin-top:24px">
    <a href="https://finadvisor.sk/#kontakt" style="background:#1d4ed8;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">
      Áno, mám záujem →
    </a>
  </p>
  <p style="margin-top:32px;color:#999;font-size:12px">Odpovedzte "unsubscribe" pre odhlásenie.</p>
</body></html>
""",
    },
    "newsletter": {
        "subject": "💡 Tip mesiaca: Ako ušetriť €180/rok na dôchodku",
        "html": """
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333">
  <h1 style="color:#1d4ed8;font-size:22px">Tip mesiaca od FinAdvisor SK</h1>
  <hr style="border:none;border-top:1px solid #eee;margin:16px 0"/>
  <h2>💡 III. pilier — štátna prémia €180/rok</h2>
  <p>Vedeli ste, že ak si mesačne odkladáte aspoň <strong>€25 do III. piliera</strong>, štát vám každý rok pridá až <strong>€180</strong>?</p>
  <p>To je garantovaný 60% výnos na vašom vklade — bez akéhokoľvek rizika.</p>
  <h3>Ako na to:</h3>
  <ol>
    <li>Otvorte si zmluvu v DDS (NN, Uniqa, Kooperativa)</li>
    <li>Nastavte mesačný príkaz min. €25</li>
    <li>Každý rok žiadajte daňový odpočet</li>
  </ol>
  <p><strong>Bonus:</strong> Ak vám prispieva aj zamestnávateľ, výnos je ešte vyšší.</p>
  <p style="margin-top:24px">
    <a href="https://finadvisor.sk/#kontakt" style="background:#1d4ed8;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">
      Chcem vedieť viac →
    </a>
  </p>
  <p style="margin-top:32px;color:#999;font-size:12px">Odpovedzte "unsubscribe" pre odhlásenie. · FinAdvisor SK</p>
</body></html>
""",
    },
}


@dataclass
class Lead:
    email: str
    full_name: str
    interest: str = "investment"
    company: Optional[str] = None

    @property
    def first_name(self) -> str:
        return self.full_name.split()[0] if self.full_name else "klient"


def load_leads(csv_path: str) -> list[Lead]:
    leads = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(Lead(
                email=row["email"].strip(),
                full_name=row.get("full_name", "").strip(),
                interest=row.get("interest", "investment").strip(),
                company=row.get("company", "").strip() or None,
            ))
    logger.info("Loaded %d leads from %s", len(leads), csv_path)
    return leads


def send_email(smtp: smtplib.SMTP, lead: Lead, template_name: str) -> bool:
    tpl = TEMPLATES[template_name]
    subject = tpl["subject"].format(first_name=lead.first_name)
    html = tpl["html"].format(first_name=lead.first_name, interest=lead.interest)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = lead.email
    msg["Reply-To"] = FROM_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        smtp.sendmail(FROM_EMAIL, lead.email, msg.as_string())
        logger.info("✓ Sent '%s' → %s", template_name, lead.email)
        return True
    except Exception as e:
        logger.error("✗ Failed → %s : %s", lead.email, e)
        return False


def run_campaign(leads_csv: str, template: str, dry_run: bool = False) -> None:
    leads = load_leads(leads_csv)
    tpl_names = list(TEMPLATES.keys())
    if template not in tpl_names:
        raise ValueError(f"Unknown template '{template}'. Choose from: {tpl_names}")

    if dry_run:
        logger.info("[DRY RUN] Would send '%s' to %d leads", template, len(leads))
        for lead in leads:
            logger.info("  → %s (%s)", lead.email, lead.first_name)
        return

    if not SMTP_USER or not SMTP_PASS:
        raise EnvironmentError("Set SMTP_USER and SMTP_PASS environment variables.")

    sent = failed = 0
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        logger.info("SMTP connected. Sending campaign '%s' to %d leads...", template, len(leads))

        for lead in leads:
            ok = send_email(smtp, lead, template)
            if ok:
                sent += 1
            else:
                failed += 1
            time.sleep(DELAY_BETWEEN_EMAILS)

    logger.info("Campaign done. Sent: %d | Failed: %d", sent, failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAdvisor SK — Email outreach")
    parser.add_argument("--list", required=True, help="Path to leads CSV file")
    parser.add_argument("--template", default="welcome", help="Template: welcome|followup|newsletter")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    args = parser.parse_args()
    run_campaign(args.list, args.template, args.dry_run)
