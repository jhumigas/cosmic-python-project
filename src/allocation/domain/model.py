from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Set, Union

from allocation.domain import commands, events


@dataclass(unsafe_hash=True)
class OrderLine:
    # Note: We used the value object pattern here to ensure that the order line is immutable.
    orderid: str
    sku: str
    qty: int


class OutOfStock(Exception):
    pass


class Batch:
    # Note: We used the entity pattern here to ensure that the batch is mutable and since they have an identity.
    def __init__(
        self, reference: str, sku: str, quantity: int, eta: Optional[date] = None
    ):
        self.reference = reference
        self.sku = sku
        self.eta: Optional[date] = eta
        self._purchased_quantity = quantity
        self._allocations: Set[OrderLine] = set()

    def __gt__(self, other: "Batch") -> bool:
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __repr__(self) -> str:
        return f"<Batch {self.reference}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    def can_allocate(self, line: OrderLine) -> bool:
        is_quantity_available: bool = self.available_quantity >= line.qty
        is_sku_valid: bool = self.sku == line.sku
        if self._allocations is not None:
            is_same_line_already_not_allocated = line not in self._allocations
        return (
            is_quantity_available
            and is_sku_valid
            and is_same_line_already_not_allocated
        )


class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events: List[Union[events.Event, commands.Command]] = []

    def allocate(self, line: OrderLine) -> Optional[str]:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            self.events.append(
                events.Allocated(
                    orderid=line.orderid,
                    sku=line.sku,
                    qty=line.qty,
                    batchref=batch.reference,
                )
            )
            return batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(sku=line.sku))
            return None

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(commands.Allocate(line.orderid, line.sku, line.qty))
