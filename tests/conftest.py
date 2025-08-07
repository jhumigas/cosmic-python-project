# pylint: disable=redefined-outer-name
import shutil
import subprocess
import time
from pathlib import Path

import pulsar
import pytest
import requests
from requests.exceptions import ConnectionError
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from tenacity import retry, stop_after_delay

from allocation.adapters.orm import metadata, start_mappers
from allocation import config


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(in_memory_db):
    yield sessionmaker(bind=in_memory_db)


@pytest.fixture
def session(session_factory):
    return session_factory()


@pytest.fixture
def sqlite_session_factory(in_memory_db):
    yield sessionmaker(bind=in_memory_db)


@pytest.fixture
def mappers():
    start_mappers()
    yield
    clear_mappers()


@pytest.fixture
def sqlite_session(sqlite_session_factory):
    return sqlite_session_factory()


def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")


def wait_for_webapp_to_come_up():
    deadline = time.time() + 10
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.5)
    pytest.fail("API never came up")


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session_factory(postgres_db):
    yield sessionmaker(bind=postgres_db)


@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()


@pytest.fixture
def restart_api():
    (Path(__file__).parent / "../src/allocation/entrypoints/fast_app.py").touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()


@retry(stop=stop_after_delay(10))
def wait_for_pulsar_to_come_up():
    pulsar_client = pulsar.Client(config.get_pulsar_uri(), operation_timeout_seconds=30)
    pulsar_client.close()
    return True


@pytest.fixture
def restart_pulsar_pubsub():
    wait_for_pulsar_to_come_up()
    if not shutil.which("docker-compose"):
        print("skipping restart, assumes running in container")
        return
    subprocess.run(
        ["docker-compose", "restart", "-t", "0", "pulsar_pubsub"],
        check=True,
    )
