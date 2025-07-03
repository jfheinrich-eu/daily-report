"""Unit tests for Markdown to HTML conversion and email attachment in DailyReporter."""

from unittest.mock import MagicMock, patch

import pytest

from daily_report.daily_reporter import DailyReporter


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
@patch("daily_report.daily_reporter.smtplib.SMTP")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_send_email_markdown_to_html_and_attachment(
    mock_openai: MagicMock,
    mock_github: MagicMock,
    mock_smtp: MagicMock,
    mock_check_env_vars: MagicMock,
) -> None:
    """Test that Markdown is converted to HTML and attached as a file in the email."""
    env = valid_env()
    mock_check_env_vars.return_value = env

    mock_openai.return_value.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=None))
    ]

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

    # Patch markdown.markdown to return valid HTML
    with patch(
        "daily_report.daily_reporter.markdown.markdown", return_value="<p>Test</p>"
    ) as mock_md:
        reporter.send_email("subject", "# Test Markdown")
        mock_md.assert_called_once_with("# Test Markdown")
        # SMTP sendmail should be called
        assert mock_smtp.return_value.__enter__.return_value.sendmail.called


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.smtplib.SMTP")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
def test_send_email_markdown_to_html_empty_raises(
    mock_openai: MagicMock,
    mock_github: MagicMock,
    mock_smtp: MagicMock,  # pylint: disable=unused-argument
    mock_check_env_vars: MagicMock,
) -> None:
    """Test that a ValueError is raised if Markdown to HTML conversion returns an empty string."""
    env = valid_env()
    mock_check_env_vars.return_value = env

    mock_openai.return_value.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=None))
    ]

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
    # Patch markdown.markdown to return empty string
    with patch("daily_report.daily_reporter.markdown.markdown", return_value=""):
        with pytest.raises(ValueError, match="Failed to convert Markdown to HTML."):
            reporter.send_email("subject", "# Test Markdown")
