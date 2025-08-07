import json
import logging
import pulsar
from allocation import bootstrap, config
from allocation.domain import commands
from allocation.service_layer.messagebus import MessageBus
import time

logger = logging.getLogger(__name__)


def main():
    logger.info("Consumer starting")
    bus = bootstrap.bootstrap()
    client = pulsar.Client(config.get_pulsar_uri(), operation_timeout_seconds=30)
    consumer = client.subscribe(
        topic="change_batch_quantity",
        subscription_name="allocation_events",
        consumer_name=f"allocation_event_consumer{time.time()}",
        schema=pulsar.schema.StringSchema(),
    )
    while True:
        msg = consumer.receive()
        try:
            logger.info(
                "Received message '{}' id='{}'".format(msg.data(), msg.message_id())
            )
            handle_change_batch_quantity(msg.data(), bus)
            # Acknowledge successful processing of the message
            consumer.acknowledge(msg)
        except Exception:
            # Message failed to be processed
            consumer.negative_acknowledge(msg)


def handle_change_batch_quantity(m, bus: MessageBus):
    logger.info("handling %s", m)
    data = json.loads(m)
    logger.info("data: %s", data)
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    bus.handle(cmd)


if __name__ == "__main__":
    main()
