from typing import Callable, Optional
from allocation.logger import logger
from allocation.adapters import notifications
from allocation.domain import commands, events, model
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
    event: commands.CreateBatch,
    uow: unit_of_work.AbstractUnitOfWork,  # (1)
):
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()


def allocate(
    event: commands.Allocate,
    uow: unit_of_work.AbstractUnitOfWork,  # (1)
) -> Optional[str]:
    line = model.OrderLine(event.orderid, event.sku, event.qty)
    logger.info("Allocating %s", line)
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line=line)
        uow.commit()
        return batchref


def reallocate(
    event: events.Deallocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(
            commands.Allocate(orderid=event.orderid, sku=event.sku, qty=event.qty)
        )
        uow.commit()


def send_out_of_stock_notification(
    event: events.OutOfStock,
    notifications: notifications.AbstractNotifications,
):
    notifications.send(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


def change_batch_quantity(
    event: commands.ChangeBatchQuantity,
    uow: unit_of_work.AbstractUnitOfWork,
):
    logger.info("Changing batch quantity for %s to %s", event.ref, event.qty)
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()


def publish_allocated_event(
    event: events.Allocated,
    publish: Callable,
):
    logger.info("Publishing allocated event for order %s", event.orderid)
    publish("line_allocated", event)
    logger.info("Published allocated event for order %s", event.orderid)


def add_allocation_to_read_model(
    event: events.Allocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        uow.execute(
            """
                INSERT INTO allocations_view (orderid, sku, batchref)
                VALUES (:orderid, :sku, :batchref)
                """,
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref),
        )
        uow.commit()


def remove_allocation_from_read_model(
    event: events.Deallocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        uow.execute(
            """
                DELETE FROM allocations_view
                WHERE orderid = :orderid AND sku = :sku
                """,
            dict(orderid=event.orderid, sku=event.sku),
        )
        uow.commit()
