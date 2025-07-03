"""This module provides the `DailyReporter` class, which generates, analyzes,
and sends daily reports of GitHub commits for a repository via email.

Main features:
- Loads and validates required environment variables for GitHub, OpenAI,
  and email configuration.
- Collects commits from the last two days from a specified GitHub repository.
- Analyzes commits using OpenAI GPT, generates a daily summary in Markdown
  format, and provides recommendations for possible issues, TODOs, or code smells.
- Sends the generated report via email
  (as Markdown text, HTML, and as an attachment).
- Saves the report locally as a Markdown file and optionally outputs it for
  GitHub Actions.

Dependencies:
- env_check (local module for environment variable validation)

Usage example:
from daily_report import DailyReporter
"""

import os
import re
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import markdown
from github import Github
from openai import OpenAI

from .env_check import EnvCheckError, check_env_vars


class DailyReporter:
    """Generates and sends a daily GitHub report via email."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self) -> None:
        try:
            env = check_env_vars()
        except EnvCheckError as exc:
            print("❌ Invalid configuration of environment variables:")
            print(exc)
            sys.exit(1)

        self.github_token: str = env["GITHUB_TOKEN"]
        self.repo_name: str = env["REPO_NAME"]
        self.email_sender: str = env["EMAIL_SENDER"]
        self.email_user: str = env["EMAIL_USER"]
        self.email_receiver: str = env["EMAIL_RECEIVER"]
        self.email_password: str = env["EMAIL_PASSWORD"]
        self.openai_api_key: str = env["OPENAI_API_KEY"]
        self.smtp_server: str = env["SMTP_SERVER"]
        self.smtp_port: int = int(env["SMTP_PORT"])

        self.client = OpenAI(api_key=self.openai_api_key)
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)

    def collect_commits(self) -> list[dict[str, Any]]:
        """Collects commits from the last 2 days."""
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
        """Analyzes commits using OpenAI GPT and returns a Markdown summary."""
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
        return "No summary generated (response was empty)."

    def send_email(self, subject: str, body_md: str) -> None:
        """Sends an email with the report as HTML and Markdown attachment."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.email_sender
        msg["To"] = self.email_receiver

        html_body = markdown.markdown(body_md)
        if not html_body:
            raise ValueError("Failed to convert Markdown to HTML.")

        html = f"""\
<html>
  <body>
    {html_body}
  </body>
</html>
"""

        part1 = MIMEText(body_md, "plain")
        part2 = MIMEText(html, "html")
        msg.attach(part1)
        msg.attach(part2)

        attachment = MIMEApplication(body_md.encode("utf-8"), Name="report.md")
        attachment["Content-Disposition"] = 'attachment; filename="report.md"'
        msg.attach(attachment)

        with smtplib.SMTP(self.smtp_server, port=self.smtp_port) as server:
            server.ehlo()
            server.starttls()
            if not self.email_password:
                raise ValueError(
                    "EMAIL_PASSWORD environment variable is not set or is empty."
                )
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_sender, self.email_receiver, msg.as_string())

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path injection."""
        # Remove directory components and allow only safe chars
        filename = os.path.basename(filename)
        filename = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
        return filename

    def run(self) -> None:
        """Runs the report generation and email sending process."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Sanitize repo_name for filename to prevent path injection
        safe_repo_name = self._sanitize_filename(self.repo_name.replace("/", "-"))
        filename = f"{today}-{safe_repo_name}.md"
        os.environ["DAILY_REPORT_FILENAME"] = filename

        subject = f"GitHub Daily Report – {self.repo_name} – {today}"

        commit_data = self.collect_commits()
        report_md = self.analyze_commits_with_gpt(commit_data)
        self.send_email(subject, report_md)

        # Save report to file (safe filename)
        with open(filename, "w", encoding="utf-8") as reportfile:
            reportfile.write(report_md)

        # Provide output for GitHub Actions
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as fh:
                print(f"report<<EOF\n{report_md}\nEOF", file=fh)

        print("✅ Report generated and sent.")
