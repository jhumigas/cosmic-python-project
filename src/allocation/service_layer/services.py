from datetime import date
from typing import Optional
from allocation.domain import model
from allocation.adapters.repository import AbstractRepository


class InvalidSku(Exception):
    pass


def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session):
    line = model.OrderLine(orderid, sku, qty)
    batches = repo.list()
    try:
        batchref = model.allocate(line, batches)
    except model.OutOfStock as e:
        raise InvalidSku(f"Invalid sku {line.sku}") from e
    session.commit()
    return batchref


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date], repo: AbstractRepository, session
):
    repo.add(model.Batch(reference=ref, sku=sku, quantity=qty, eta=eta))
    session.commit()
