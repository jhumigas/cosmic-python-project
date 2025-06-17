from dataclasses import dataclass
from datetime import date
from typing import Optional, Set


@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(
        self, reference: str, sku: str, quantity: int, eta: Optional[date] = None
    ):
        self.reference = reference
        self.sku = sku
        self.quantity = quantity
        self.eta = eta
        self.allocations: Set[OrderLine] = set()

    @property
    def available_quantity(self) -> int:
        return self.quantity - sum(line.qty for line in self.allocations)

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self.quantity -= line.qty

    def can_allocate(self, line: OrderLine) -> bool:
        is_quantity_available: bool = self.available_quantity >= line.qty
        is_sku_valid: bool = self.sku == line.sku
        if self.allocations is not None:
            is_same_line_already_not_allocated = line not in self.allocations
        return (
            is_quantity_available
            and is_sku_valid
            and is_same_line_already_not_allocated
        )
