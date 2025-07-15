import json
import logging
import pulsar
from allocation import bootstrap, config
from allocation.domain import commands
from allocation.service_layer.messagebus import MessageBus

logger = logging.getLogger(__name__)


def main():
    logger.info("Consumer starting")
    bus = bootstrap.bootstrap()
    client = pulsar.Client(config.get_pulsar_uri())
    consumer = client.subscribe("change-batch-quantity", "allocation-consumer")
    while True:
        msg = consumer.receive()
        try:
            logger.debug(
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
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    bus.handle(cmd)


if __name__ == "__main__":
    main()
