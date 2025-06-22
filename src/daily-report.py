# GitHub Daily Report Generator (Markdown + Email)

import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from github import Github
from openai import OpenAI

from env_check import EnvCheckError, check_env_vars

try:
    env = check_env_vars()
except EnvCheckError as e:
    print("❌ Fehlerhafte Konfiguration der Umgebungsvariablen:")
    print(e)
    import sys

    sys.exit(1)

GITHUB_TOKEN = env["GITHUB_TOKEN"]
REPO_NAME = env["REPO_NAME"]
EMAIL_SENDER = env["EMAIL_SENDER"]
EMAIL_USER = env["EMAIL_USER"]
EMAIL_RECEIVER = env["EMAIL_RECEIVER"]
EMAIL_PASSWORD = env["EMAIL_PASSWORD"]
OPENAI_API_KEY = env["OPENAI_API_KEY"]
SMTP_SERVER = env["SMTP_SERVER"]
SMTP_PORT = int(env["SMTP_PORT"])

client = OpenAI(api_key=OPENAI_API_KEY)

# === Initialisierung ===
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
since = datetime.now(timezone.utc) - timedelta(days=2)

# === Änderungen sammeln ===
commits = repo.get_commits(since=since)

commit_data: list[dict[str, Any]] = []
for commit in commits:
    commit_data.append(
        {
            "message": commit.commit.message,
            "author": commit.commit.author.name,
            "url": commit.html_url,
            "sha": commit.sha,
            "date": commit.commit.author.date,
        }
    )

# === GPT-Analyse ===


def analyze_commits_with_gpt(commits: list[dict[str, Any]]):
    if not commits:
        return "Keine Commits in den letzten 24h."

    formatted = "\n".join(
        f"- [{c['sha'][:7]}] {c['message']} ({c['author']})" for c in commits
    )
    prompt = f"""
Hier ist eine Liste von Git-Commits:
{formatted}

Erstelle eine tägliche Zusammenfassung in Markdown.
Analysiere mögliche Probleme, TODOs oder Code-Smells und gib Empfehlungen.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    content = response.choices[0].message.content
    if content is not None:
        return content.strip()
    else:
        return "Keine Zusammenfassung generiert (Antwort war leer)."


report_md = analyze_commits_with_gpt(commit_data)

# === Report als E-Mail senden ===


def send_email(subject: str, body_md: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    html = f"""
    <html>
      <body>
        <pre style='font-family: monospace;'>{body_md}</pre>
      </body>
    </html>
    """

    part1 = MIMEText(body_md, "plain")
    part2 = MIMEText(html, "html")
    msg.attach(part1)
    msg.attach(part2)

    with smtplib.SMTP(SMTP_SERVER, port=SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        if not EMAIL_PASSWORD:
            raise ValueError(
                "EMAIL_PASSWORD environment variable is not set or is empty."
            )
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())


# === Ausführen ===
heute = datetime.now(timezone.utc).strftime("%Y-%m-%d")
subject = f"GitHub Daily Report – {REPO_NAME} – {heute}"
filename = f"{heute}-{REPO_NAME.replace('/', '-')}.md"

send_email(subject, report_md)

# with open(filename, 'w') as reportfile:
#     reportfile.write(report_md)

print("✅ Report generiert und gesendet.")
