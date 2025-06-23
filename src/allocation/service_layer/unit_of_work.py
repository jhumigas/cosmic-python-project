from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from allocation.adapters import repository
from allocation import config
import abc

from allocation.service_layer import messagebus


class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractRepository  # (1)

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):  # (2)
        self.rollback()  # (4)

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                messagebus.handle(event)

    def commit(self):  # (3)
        self._commit()
        self.publish_events()

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):  # (4)
        raise NotImplementedError


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(
        config.get_postgres_uri(),
        isolation_level="REPEATABLE READ",
    )
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()  # (3)

    def _commit(self):  # (4)
        self.session.commit()

    def rollback(self):  # (4)
        self.session.rollback()
