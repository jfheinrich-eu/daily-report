import os
from github import Github


class EnvCheckError(Exception):
    pass


def check_env_vars() -> dict[str, str]:
    """
    Prüft alle benötigten Umgebungsvariablen und gibt ein Dict mit Namen und Wert zurück.
    Bei Fehlern wird eine EnvCheckError Exception geworfen.
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
            errors.append(f"{key} ist nicht gesetzt.")

    # Plausibilität prüfen
    if env["REPO_NAME"] and env["GITHUB_TOKEN"]:
        try:
            g = Github(env["GITHUB_TOKEN"])
            g.get_repo(env["REPO_NAME"])
        except Exception as e:
            errors.append(
                f"REPO_NAME '{env['REPO_NAME']}' ist ungültig oder nicht erreichbar: {e}")

    if env["SMTP_PORT"]:
        try:
            port = int(env["SMTP_PORT"])
            if not (0 < port < 65536):
                errors.append(
                    f"SMTP_PORT '{env['SMTP_PORT']}' ist keine gültige Portnummer.")
        except ValueError:
            errors.append(f"SMTP_PORT '{env['SMTP_PORT']}' ist keine Zahl.")

    if errors:
        raise EnvCheckError("\n".join(errors))

    return env
