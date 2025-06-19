from allocation import model
from allocation.repository import AbstractRepository


class InvalidSku(Exception):
    pass


def allocate(line: model.OrderLine, repo: AbstractRepository, session):
    batches = repo.list()
    try:
        batchref = model.allocate(line, batches)
    except model.OutOfStock as e:
        raise InvalidSku(f"Invalid sku {line.sku}") from e
    session.commit()
    return batchref
