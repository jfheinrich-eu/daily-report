import os
from unittest.mock import MagicMock, patch

from daily_report.daily_reporter import DailyReporter


def valid_env():
    return {
        "GITHUB_TOKEN": "token",
        "REPO_NAME": "owner/repo",
        "EMAIL_SENDER": "sender@example.com",
        "EMAIL_USER": "sender@example.com",
        "EMAIL_RECEIVER": "receiver@example.com",
        "EMAIL_PASSWORD": "pw",
        "OPENAI_API_KEY": "sk-xxx",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
    }


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_run_sends_email(
    mock_openai: MagicMock, mock_github: MagicMock, mock_check_env_vars: MagicMock
):
    # Arrange
    env = valid_env()
    for k, v in env.items():
        os.environ[k] = v
    mock_check_env_vars.return_value = env

    mock_repo = MagicMock()
    mock_commit = MagicMock()
    mock_commit.commit.message = "fix: bug"
    mock_commit.commit.author.name = "dev"
    mock_commit.html_url = "http://example.com"
    mock_commit.sha = "abc1234"
    mock_commit.commit.author.date = "2024-01-01"
    mock_repo.get_commits.return_value = [mock_commit]
    mock_github.return_value.get_repo.return_value = mock_repo

    mock_openai.return_value.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Test-Report"))
    ]

    # Patch smtplib.SMTP
    with patch("daily_report.daily_reporter.smtplib.SMTP") as _mock_smtp:
        reporter = DailyReporter()
        reporter.run()


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_analyze_commits_with_gpt_empty(
    mock_openai: MagicMock, mock_github: MagicMock, mock_check_env_vars: MagicMock
):
    env = valid_env()
    for k, v in env.items():
        os.environ[k] = v
    mock_check_env_vars.return_value = env
    reporter = DailyReporter()
    result = reporter.analyze_commits_with_gpt([])
    assert "No commits" in result
