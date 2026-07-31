import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_VALIDATION_MESSAGE = "Please enter a valid email address."


def is_gmail_address(email):
    if not isinstance(email, str):
        return False

    normalized_email = email.strip().lower()
    return bool(EMAIL_RE.fullmatch(normalized_email))


def get_gmail_validation_message():
    return EMAIL_VALIDATION_MESSAGE
