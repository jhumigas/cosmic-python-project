import abc
from typing import Set
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


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, product):  # (2)
        self.session.add(product)

    def _get(self, sku):  # (3)
        return self.session.query(model.Product).filter_by(sku=sku).first()
