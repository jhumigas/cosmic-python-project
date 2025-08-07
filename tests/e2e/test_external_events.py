import json
import pytest
from tenacity import Retrying, stop_after_delay

from allocation.logger import logger
from . import api_client, pulsar_client
from ..random_refs import random_batchref, random_orderid, random_sku


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("restart_pulsar_pubsub")
def test_change_batch_quantity_leading_to_reallocation():
    # start with two batches and an order allocated to one of them
    orderid, sku = random_orderid(), random_sku()
    earlier_batch, later_batch = random_batchref("old"), random_batchref("newer")
    api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta="2011-01-01")
    api_client.post_to_add_batch(later_batch, sku, qty=10, eta="2011-01-02")
    r = api_client.post_to_allocate(orderid, sku, 10)
    assert r.ok
    response = api_client.get_allocation(orderid)
    assert response.json()[0]["batchref"] == earlier_batch

    subscription = pulsar_client.subscribe_to("line_allocated")
    # change quantity on allocated batch so it's less than our order
    pulsar_client.publish_message(
        "change_batch_quantity",
        {"batchref": earlier_batch, "qty": 5},
    )

    # wait until we see a message saying the order has been reallocated
    for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = subscription.receive()
            subscription.acknowledge(message)
            data = json.loads(message.data())
            logger.info("Received message: %s", data)
            assert data["orderid"] == orderid
            assert data["batchref"] in (earlier_batch, later_batch)
    subscription.close()
