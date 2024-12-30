import base64
import secrets


def generate_secret(token_bytes: int = 16) -> str:
    """Generate a string that can be used as a secret key."""
    random_bytes = secrets.token_bytes(token_bytes)
    secret_key = base64.b64encode(random_bytes).decode("utf-8")
    return secret_key


if __name__ == "__main__":
    print(generate_secret())
