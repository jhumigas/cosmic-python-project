from datetime import date, timedelta
import pytest
from allocation.domain import model
from allocation.service_layer import services, unit_of_work
from allocation.adapters.repository import FakeRepository


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.batches = FakeRepository([])  # (1)
        self.committed = False  # (2)

    def commit(self):
        self.committed = True  # (2)

    def rollback(self):
        pass


# domain-layer test:
def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = model.OrderLine("oref", "RETRO-CLOCK", 10)

    model.allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_warehouse_batches_to_shipments():
    # in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    # shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    uow = FakeUnitOfWork()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, None, uow)
    services.add_batch("shipment-batch", "RETRO-CLOCK", 100, tomorrow, uow)
    in_stock_batch = uow.batches.get("in-stock-batch")
    shipment_batch = uow.batches.get("shipment-batch")

    services.allocate(orderid="oref", sku="RETRO-CLOCK", qty=10, uow=uow)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", 100, None, uow)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits():
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    uow = FakeUnitOfWork()
    uow.batches.add(batch)

    services.allocate(orderid="o1", sku="OMINOUS-MIRROR", qty=10, uow=uow)
    assert uow.committed is True


def test_add_batch():
    uow = FakeUnitOfWork()  # (3)
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)  # (3)
    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()  # (3)
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)  # (3)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)  # (3)
    assert result == "batch1"
