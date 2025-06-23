from dataclasses import dataclass
from datetime import date
from typing import Optional


class Command:
    pass


@dataclass
class Allocate(Command):  # (1)
    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):  # (2)
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass
class ChangeBatchQuantity(Command):  # (3)
    ref: str
    qty: int
