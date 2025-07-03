"""Unit test for verifying GitHub Actions output file integration in DailyReporter."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from daily_report.daily_reporter import DailyReporter


@patch("daily_report.daily_reporter.check_env_vars")
@patch("daily_report.daily_reporter.Github")
@patch("daily_report.daily_reporter.OpenAI")
@patch("daily_report.daily_reporter.smtplib.SMTP")
def test_github_output_written(
    mock_smtp: MagicMock,  # pylint: disable=unused-argument
    mock_openai: MagicMock,
    mock_github: MagicMock,
    mock_check_env_vars: MagicMock,
) -> None:
    """Test that the GitHub Actions output file is written with the report content."""
    env = {
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
    mock_check_env_vars.return_value = env

    mock_repo = MagicMock()
    mock_commit = MagicMock()
    mock_commit.commit.message = "test"
    mock_commit.commit.author.name = "author"
    mock_commit.html_url = "http://example.com"
    mock_commit.sha = "sha"
    mock_commit.commit.author.date = "2024-01-01"
    mock_repo.get_commits.return_value = [mock_commit]
    mock_github.return_value.get_repo.return_value = mock_repo

    mock_openai.return_value.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Test-Report"))
    ]

    with tempfile.NamedTemporaryFile(mode="r+", delete=False) as tmpfile:
        os.environ["GITHUB_OUTPUT"] = tmpfile.name
        reporter = DailyReporter()
        reporter.run()
        tmpfile.seek(0)
        content = tmpfile.read()
        assert "Test-Report" in content

    # Clean up: remove the file
    filename = os.environ.get("DAILY_REPORT_FILENAME")
    assert filename is not None
    assert os.path.exists(filename)
    os.remove(filename)
    assert not os.path.exists(filename)
