import os
from github import Github


class EnvCheckError(Exception):
    pass


def check_env_vars() -> dict[str, str]:
    """
    Checks all required environment variables and returns a dict with their names and values.
    Raises EnvCheckError if any variable is missing or invalid.
    """
    env = {
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
        "REPO_NAME": os.getenv("REPO_NAME", ""),
        "EMAIL_SENDER": os.getenv("EMAIL_SENDER", ""),
        "EMAIL_USER": os.getenv("EMAIL_USER", os.getenv("EMAIL_SENDER", "")),
        "EMAIL_RECEIVER": os.getenv("EMAIL_RECEIVER", ""),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "SMTP_SERVER": os.getenv("SMTP_SERVER", ""),
        "SMTP_PORT": os.getenv("SMTP_PORT", ""),
    }

    errors: list[str] = []
    for key, value in env.items():
        if not value:
            errors.append(f"{key} is not set.")

    # Plausibility checks
    if env["REPO_NAME"] and env["GITHUB_TOKEN"]:
        try:
            g = Github(env["GITHUB_TOKEN"])
            g.get_repo(env["REPO_NAME"])
        except Exception as e:
            errors.append(
                f"REPO_NAME '{env['REPO_NAME']}' is invalid or not accessible: {e}"
            )

    if env["SMTP_PORT"]:
        try:
            port = int(env["SMTP_PORT"])
            if not (0 < port < 65536):
                errors.append(
                    f"SMTP_PORT '{env['SMTP_PORT']}' is not a valid port number."
                )
        except ValueError:
            errors.append(f"SMTP_PORT '{env['SMTP_PORT']}' is not a number.")

    if errors:
        raise EnvCheckError("\n".join(errors))

    return env
