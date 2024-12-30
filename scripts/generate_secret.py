import base64
import secrets


def generate_secret():
    random_bytes = secrets.token_bytes(16)
    secret_key = base64.b64encode(random_bytes).decode("utf-8")
    return secret_key


if __name__ == "__main__":
    print(generate_secret())
