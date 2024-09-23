import os


def list_flask_env():
    print("Flask Environment Variables:")
    for key, value in os.environ.items():
        if key.startswith("FLASK_"):
            print(f"{key}: {value}")


if __name__ == "__main__":
    list_flask_env()
