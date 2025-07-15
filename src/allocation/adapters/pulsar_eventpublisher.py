from dataclasses import asdict
import pulsar
import json

from allocation import config
from allocation.logger import logger
from allocation.domain import events

client = pulsar.Client(config.get_pulsar_uri())
producer = client.create_producer(topic="change-batch-quantity")


def publish(channel, event: events.Event):
    logger.debug("publishing: channel=%s, event=%s", channel, event)
    producer.send(channel, json.dumps(asdict(event)))
