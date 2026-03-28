#!/usr/bin/env python3
"""
Marketing Cron Scheduler — FinAdvisor SK

Runs daily automated tasks:
  - 09:00  Post tip of the week to all social platforms
  - 10:00  Send follow-up emails to leads not contacted in 3 days
  - 18:00  Post promo on social media (Mon/Thu only)

Usage:
    # Run once manually:
    python marketing/cron.py --now

    # Start scheduler (blocks, runs indefinitely):
    python marketing/cron.py

    # Add to crontab for system-level scheduling:
    # 0 9 * * * cd /path/to/project && .venv/bin/python marketing/cron.py --now --task social_tip
"""
import os
import sys
import time
import logging
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("cron")


def task_social_tip():
    logger.info("Running: post tip_of_week to social media")
    from marketing.social.auto_post import run
    run(platform="all", post_key="tip_of_week")


def task_social_promo():
    today = datetime.now().weekday()  # 0=Mon, 3=Thu
    if today not in (0, 3):
        logger.info("Promo skipped — only runs Mon/Thu")
        return
    logger.info("Running: post promo to social media")
    from marketing.social.auto_post import run
    run(platform="all", post_key="promo")


def task_email_followup():
    """Send followup to leads CSV if exists."""
    leads_file = os.path.join(os.path.dirname(__file__), "email", "leads.csv")
    if not os.path.exists(leads_file):
        logger.info("No leads.csv found, skipping email followup")
        return
    logger.info("Running: email followup campaign")
    from marketing.email.send_outreach import run_campaign
    run_campaign(leads_file, "followup")


TASKS = {
    "social_tip": task_social_tip,
    "social_promo": task_social_promo,
    "email_followup": task_email_followup,
}

SCHEDULE = [
    {"hour": 9,  "minute": 0,  "task": "social_tip"},
    {"hour": 10, "minute": 0,  "task": "email_followup"},
    {"hour": 18, "minute": 0,  "task": "social_promo"},
]


def run_scheduler():
    logger.info("Scheduler started. Waiting for scheduled tasks...")
    last_run: dict[str, str] = {}

    while True:
        now = datetime.now()
        time_key = now.strftime("%Y-%m-%d %H:%M")

        for job in SCHEDULE:
            if now.hour == job["hour"] and now.minute == job["minute"]:
                task_name = job["task"]
                run_key = f"{time_key}_{task_name}"
                if last_run.get(task_name) != run_key:
                    logger.info("Triggering task: %s", task_name)
                    try:
                        TASKS[task_name]()
                    except Exception:
                        logger.exception("Task '%s' failed", task_name)
                    last_run[task_name] = run_key

        time.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAdvisor SK marketing cron")
    parser.add_argument("--now", action="store_true", help="Run all tasks immediately and exit")
    parser.add_argument("--task", help=f"Run specific task: {list(TASKS.keys())}")
    args = parser.parse_args()

    if args.task:
        if args.task not in TASKS:
            print(f"Unknown task. Available: {list(TASKS.keys())}")
            sys.exit(1)
        TASKS[args.task]()
    elif args.now:
        for name, fn in TASKS.items():
            logger.info("Running task: %s", name)
            try:
                fn()
            except Exception:
                logger.exception("Task '%s' failed", name)
    else:
        run_scheduler()
