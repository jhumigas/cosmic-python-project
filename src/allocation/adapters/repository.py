import abc
from typing import Set
from allocation.adapters import orm
from allocation.domain import model


class AbstractRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[model.Product] = set()

    @abc.abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    @abc.abstractmethod  # (3)
    def _get(self, sku) -> model.Product:
        raise NotImplementedError

    def get(self, sku) -> model.Product:  # (3)
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, batchref) -> model.Product:
        product = self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _get_by_batchref(self, batchref) -> model.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, product):  # (2)
        self.session.add(product)

    def _get(self, sku):  # (3)
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def _get_by_batchref(self, batchref):
        return (
            self.session.query(model.Product)
            .join(model.Batch)
            .filter(orm.batches.c.reference == batchref)
            .first()
        )
