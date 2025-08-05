import json
import time
import pulsar

from allocation import config
from allocation.logger import logger


def subscribe_to(channel):
    logger.info("Subscribing to channel: %s", channel)
    pulsar_client_consumer = pulsar.Client(config.get_pulsar_uri())
    consumer = pulsar_client_consumer.subscribe(
        topic=channel,
        subscription_name="allocation_test",
        consumer_name=f"allocation_consumer_test{time.time()}",
        schema=pulsar.schema.StringSchema(),
    )
    return consumer


def publish_message(channel, message):
    pulsar_client = pulsar.Client(config.get_pulsar_uri())
    producer = pulsar_client.create_producer(
        topic=channel,
        schema=pulsar.schema.StringSchema(),
        producer_name=f"allocation_producer_test{time.time()}",
    )
    logger.debug("publishing: channel=%s, message=%s", channel, message)
    producer.send(content=json.dumps(message))
    producer.flush()
    producer.close()
