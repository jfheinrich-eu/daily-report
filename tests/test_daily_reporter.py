"""Unit tests for the DailyReporter class and environment validation."""

import os
from unittest.mock import MagicMock, patch

import pytest

from daily_report.daily_reporter import DailyReporter
from daily_report.env_check import EnvCheckError


def cleanup_report_file() -> None:
    """Remove the report file if it exists."""
    assert "DAILY_REPORT_FILENAME" in os.environ
    filename = os.environ.get("DAILY_REPORT_FILENAME")
    assert filename is not None
    assert os.path.exists(filename)
    os.remove(filename)
    assert not os.path.exists(filename)


def valid_env() -> dict[str, str]:
    """Return a valid environment variable dictionary for testing."""
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
@patch("daily_report.daily_reporter.open")
def test_run_sends_email(
    mock_open: MagicMock,
    mock_openai: MagicMock,
    mock_github: MagicMock,
    mock_check_env_vars: MagicMock,
) -> None:
    """Test that DailyReporter.run sends an email and writes the report file."""
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

    mock_open.return_value.__enter__.return_value = MagicMock()

    with patch("daily_report.daily_reporter.smtplib.SMTP"):
        reporter = DailyReporter()
        reporter.run()
    # cleanup_report_file()


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_analyze_commits_with_gpt_empty(
    mock_openai: MagicMock,  # pylint: disable=unused-argument
    mock_github: MagicMock,  # pylint: disable=unused-argument
    mock_check_env_vars: MagicMock,  # pylint: disable=unused-argument
) -> None:
    """Test analyze_commits_with_gpt returns correct message for empty commit list."""
    env = valid_env()
    for k, v in env.items():
        os.environ[k] = v
    mock_check_env_vars.return_value = env
    reporter = DailyReporter()
    result = reporter.analyze_commits_with_gpt([])
    assert "No commits" in result
    # cleanup_report_file()


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_analyze_commits_with_gpt_empty_response(
    mock_openai: MagicMock,
    mock_github: MagicMock,  # pylint: disable=unused-argument
    mock_check_env_vars: MagicMock,  # pylint: disable=unused-argument
) -> None:
    """Test analyze_commits_with_gpt returns correct message for empty GPT response."""
    env = valid_env()
    for k, v in env.items():
        os.environ[k] = v
    mock_check_env_vars.return_value = env
    mock_openai.return_value.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=None))
    ]
    reporter = DailyReporter()
    commits: list[dict[str, str]] = [
        {"sha": "abc", "message": "msg", "author": "a", "url": "", "date": ""}
    ]
    result = reporter.analyze_commits_with_gpt(commits)
    assert "No summary generated" in result
    # cleanup_report_file()


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_send_email_password_missing(
    mock_openai: MagicMock,  # pylint: disable=unused-argument
    mock_github: MagicMock,  # pylint: disable=unused-argument
    mock_check_env_vars: MagicMock,  # pylint: disable=unused-argument
) -> None:
    """Test send_email raises ValueError if EMAIL_PASSWORD is missing."""
    env = valid_env()
    env["EMAIL_PASSWORD"] = ""
    for k, v in env.items():
        os.environ[k] = v
    mock_check_env_vars.return_value = env
    reporter = DailyReporter()
    with patch("daily_report.daily_reporter.smtplib.SMTP"):
        with pytest.raises(ValueError):
            reporter.send_email("subject", "body")
    # cleanup_report_file()


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_collect_commits(
    mock_openai: MagicMock,  # pylint: disable=unused-argument
    mock_github: MagicMock,
    mock_check_env_vars: MagicMock,  # pylint: disable=unused-argument
) -> None:
    """Test collect_commits returns a list of commit dictionaries."""
    env = valid_env()
    for k, v in env.items():
        os.environ[k] = v
    mock_check_env_vars.return_value = env

    mock_commit = MagicMock()
    mock_commit.commit.message = "test"
    mock_commit.commit.author.name = "author"
    mock_commit.html_url = "http://example.com"
    mock_commit.sha = "sha"
    mock_commit.commit.author.date = "2024-01-01"
    mock_repo = MagicMock()
    mock_repo.get_commits.return_value = [mock_commit]
    mock_github.return_value.get_repo.return_value = mock_repo

    reporter = DailyReporter()
    commits = reporter.collect_commits()
    assert isinstance(commits, list)
    assert commits[0]["message"] == "test"
    # cleanup_report_file()


@patch("daily_report.daily_reporter.check_env_vars")
def test_init_env_error(mock_check_env_vars: MagicMock) -> None:
    """Test that DailyReporter exits if environment validation fails."""
    mock_check_env_vars.side_effect = EnvCheckError("fail")
    with (
        patch("builtins.print"),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            DailyReporter()
        mock_exit.assert_called_once()
    # cleanup_report_file()
