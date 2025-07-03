"""Unit tests for environment variable validation in the Daily Reporter project."""

import os
from unittest.mock import MagicMock, patch

import pytest
from github.GithubException import GithubException

from daily_report.env_check import EnvCheckError, check_env_vars


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically clear all relevant environment variables before each test."""
    keys = [
        "GITHUB_TOKEN",
        "REPO_NAME",
        "EMAIL_SENDER",
        "EMAIL_USER",
        "EMAIL_RECEIVER",
        "EMAIL_PASSWORD",
        "OPENAI_API_KEY",
        "SMTP_SERVER",
        "SMTP_PORT",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def valid_env() -> dict[str, str]:
    """Return a dictionary with valid environment variables for testing."""
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


@patch("daily_report.env_check.Github")
def test_check_env_vars_success(
    mock_github: MagicMock,
    monkeypatch: pytest.MonkeyPatch,  # pylint: disable=unused-argument
) -> None:
    """Test that check_env_vars returns the environment dictionary if all variables are valid."""
    env = valid_env()
    for k, v in env.items():
        os.environ[k] = v
    mock_repo = MagicMock()
    mock_github.return_value.get_repo.return_value = mock_repo

    result = check_env_vars()
    assert result == env


@patch("daily_report.env_check.Github")
def test_missing_env_vars_raises(
    mock_github: MagicMock,  # pylint: disable=unused-argument
    monkeypatch: pytest.MonkeyPatch,  # pylint: disable=unused-argument
) -> None:
    """Test that check_env_vars raises EnvCheckError if a required variable is missing."""
    env = valid_env()
    for k, v in env.items():
        if k != "REPO_NAME":
            os.environ[k] = v
    with pytest.raises(EnvCheckError) as excinfo:
        check_env_vars()
    assert "REPO_NAME is not set." in str(excinfo.value)


@patch("daily_report.env_check.Github")
def test_invalid_repo_raises(
    mock_github: MagicMock,
    monkeypatch: pytest.MonkeyPatch,  # pylint: disable=unused-argument
) -> None:
    """Test that check_env_vars raises EnvCheckError if the repository
    is invalid or inaccessible."""
    env = valid_env()
    for k, v in env.items():
        os.environ[k] = v
    # Raise GithubException instead of generic Exception
    mock_github.return_value.get_repo.side_effect = GithubException(
        404, "not found", None
    )
    with pytest.raises(EnvCheckError) as excinfo:
        check_env_vars()
    assert "invalid or not accessible" in str(excinfo.value)


@patch("daily_report.env_check.Github")
def test_invalid_smtp_port_nonint(
    mock_github: MagicMock,
    monkeypatch: pytest.MonkeyPatch,  # pylint: disable=unused-argument
) -> None:
    """Test that check_env_vars raises EnvCheckError if SMTP_PORT is not an integer."""
    env = valid_env()
    env["SMTP_PORT"] = "abc"
    for k, v in env.items():
        os.environ[k] = v
    mock_github.return_value.get_repo.return_value = MagicMock()
    with pytest.raises(EnvCheckError) as excinfo:
        check_env_vars()
    assert "SMTP_PORT 'abc' is not a number." in str(excinfo.value)


@patch("daily_report.env_check.Github")
def test_invalid_smtp_port_range(
    mock_github: MagicMock,
    monkeypatch: pytest.MonkeyPatch,  # pylint: disable=unused-argument
) -> None:
    """Test that check_env_vars raises EnvCheckError if SMTP_PORT is out of valid range."""
    env = valid_env()
    env["SMTP_PORT"] = "70000"
    for k, v in env.items():
        os.environ[k] = v
    mock_github.return_value.get_repo.return_value = MagicMock()
    with pytest.raises(EnvCheckError) as excinfo:
        check_env_vars()
    assert "SMTP_PORT '70000' is not a valid port number." in str(excinfo.value)


@patch("daily_report.env_check.Github")
def test_all_env_vars_missing(
    mock_github: MagicMock,  # pylint: disable=unused-argument
    monkeypatch: pytest.MonkeyPatch,  # pylint: disable=unused-argument
) -> None:
    """Test that check_env_vars raises EnvCheckError and reports all
    missing variables if none are set."""
    # No env vars set at all
    with pytest.raises(EnvCheckError) as excinfo:
        check_env_vars()
    # Check that multiple errors are reported
    msg = str(excinfo.value)
    assert "GITHUB_TOKEN is not set." in msg
    assert "REPO_NAME is not set." in msg
    assert "EMAIL_SENDER is not set." in msg
    assert "EMAIL_RECEIVER is not set." in msg
    assert "EMAIL_PASSWORD is not set." in msg
    assert "OPENAI_API_KEY is not set." in msg
    assert "SMTP_SERVER is not set." in msg
    assert "SMTP_PORT is not set." in msg
