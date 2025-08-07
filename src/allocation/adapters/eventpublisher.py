from dataclasses import asdict
import time
import pulsar
import json

from allocation import config
from allocation.logger import logger
from allocation.domain import events


def publish(channel, event: events.Event):
    client = pulsar.Client(config.get_pulsar_uri(), operation_timeout_seconds=30)
    logger.info("Pulsar client initialized")
    producer = client.create_producer(
        topic=channel,
        producer_name=f"allocation_producer{time.time()}",
        schema=pulsar.schema.StringSchema(),
    )
    logger.debug("publishing: channel=%s, event=%s", channel, event)
    producer.send(content=json.dumps(asdict(event)))
    producer.flush()
    producer.close()
