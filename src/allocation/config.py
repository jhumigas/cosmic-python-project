import os

# TODO: use pydantic environment variables to validate the environment variables


def get_postgres_uri():
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", 54321)
    password = os.environ.get("DB_PASSWORD", "abc123")
    user, db_name = "allocation", "allocation"
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_api_url():
    host = os.environ.get("API_HOST", "localhost")
    port = os.environ.get("API_PORT", 8000)
    return f"http://{host}:{port}"


def get_pulsar_uri():
    host = os.environ.get("PULSAR_HOST", "localhost")
    port = os.environ.get("PULSAR_PORT", 6651)
    return f"pulsar://{host}:{port}"


def get_email_host_and_port():
    host = os.environ.get("EMAIL_HOST", "localhost")
    port = os.environ.get("EMAIL_PORT", 11025)
    http_port = 18025 if host == "localhost" else 8025
    return dict(host=host, port=port, http_port=http_port)
