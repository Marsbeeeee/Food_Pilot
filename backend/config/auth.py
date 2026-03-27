import os


AUTH_SECRET = os.getenv("AUTH_SECRET", "foodpilot-dev-secret")
AUTH_TOKEN_EXPIRE_SECONDS = int(os.getenv("AUTH_TOKEN_EXPIRE_SECONDS", "604800"))
PASSWORD_HASH_ITERATIONS = int(os.getenv("PASSWORD_HASH_ITERATIONS", "120000"))


def get_admin_emails() -> set[str]:
    raw_value = os.getenv("ADMIN_EMAILS", "")
    return {
        email.strip().lower()
        for email in raw_value.split(",")
        if email.strip()
    }
