from datetime import date, timedelta
import pytest
from allocation.domain import model
from allocation.service_layer import services
from allocation.adapters.repository import FakeRepository


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


# domain-layer test:
def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = model.OrderLine("oref", "RETRO-CLOCK", 10)

    model.allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


# service-layer test:
def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed


def test_prefers_warehouse_batches_to_shipments():
    # in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    # shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, None, repo, session)
    services.add_batch("shipment-batch", "RETRO-CLOCK", 100, tomorrow, repo, session)
    in_stock_batch = repo.get("in-stock-batch")
    shipment_batch = repo.get("shipment-batch")

    services.allocate(
        orderid="oref", sku="RETRO-CLOCK", qty=10, repo=repo, session=session
    )

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, repo, session)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())


def test_commits():
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(
        orderid="o1", sku="OMINOUS-MIRROR", qty=10, repo=repo, session=session
    )
    assert session.committed is True
