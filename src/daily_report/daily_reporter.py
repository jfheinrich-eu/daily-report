import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from github import Github
from openai import OpenAI

from .env_check import EnvCheckError, check_env_vars


class DailyReporter:
    def __init__(self):
        try:
            env = check_env_vars()
        except EnvCheckError as e:
            print("❌ Invalid configuration of environment variables:")
            print(e)
            import sys

            sys.exit(1)

        self.GITHUB_TOKEN = env["GITHUB_TOKEN"]
        self.REPO_NAME = env["REPO_NAME"]
        self.EMAIL_SENDER = env["EMAIL_SENDER"]
        self.EMAIL_USER = env["EMAIL_USER"]
        self.EMAIL_RECEIVER = env["EMAIL_RECEIVER"]
        self.EMAIL_PASSWORD = env["EMAIL_PASSWORD"]
        self.OPENAI_API_KEY = env["OPENAI_API_KEY"]
        self.SMTP_SERVER = env["SMTP_SERVER"]
        self.SMTP_PORT = int(env["SMTP_PORT"])

        self.client = OpenAI(api_key=self.OPENAI_API_KEY)
        self.github = Github(self.GITHUB_TOKEN)
        self.repo = self.github.get_repo(self.REPO_NAME)

    def collect_commits(self):
        since = datetime.now(timezone.utc) - timedelta(days=2)
        commits = self.repo.get_commits(since=since)
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
        return commit_data

    def analyze_commits_with_gpt(self, commits: list[dict[str, Any]]) -> str:
        if not commits:
            return "No commits in the last 24 hours."

        formatted = "\n".join(
            f"- [{c['sha'][:7]}] {c['message']} ({c['author']})" for c in commits
        )
        prompt = f"""
Here is a list of Git commits:
{formatted}

Create a daily summary in Markdown.
Analyze possible issues, TODOs, or code smells and provide recommendations.
"""

        response = self.client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        content = response.choices[0].message.content
        if content is not None:
            return content.strip()
        else:
            return "No summary generated (response was empty)."

    def send_email(self, subject: str, body_md: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.EMAIL_SENDER
        msg["To"] = self.EMAIL_RECEIVER

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

        with smtplib.SMTP(self.SMTP_SERVER, port=self.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            if not self.EMAIL_PASSWORD:
                raise ValueError(
                    "EMAIL_PASSWORD environment variable is not set or is empty."
                )
            server.login(self.EMAIL_USER, self.EMAIL_PASSWORD)
            server.sendmail(self.EMAIL_SENDER, self.EMAIL_RECEIVER, msg.as_string())

    def run(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        subject = f"GitHub Daily Report – {self.REPO_NAME} – {today}"
        filename = f"{today}-{self.REPO_NAME.replace('/', '-')}.md"
        os.environ["DAILY_REPORT_FILENAME"] = filename

        commit_data = self.collect_commits()
        report_md = self.analyze_commits_with_gpt(commit_data)
        self.send_email(subject, report_md)

        # Save report to file
        with open(filename, "w") as reportfile:
            reportfile.write(report_md)

        # Provide output for GitHub Actions
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as fh:
                print(f"report<<EOF\n{report_md}\nEOF", file=fh)

        print("✅ Report generated and sent.")
