from typing import List, Union
from allocation.logger import logger
from allocation.domain import commands, events
from allocation.service_layer import unit_of_work
from allocation.service_layer import handlers


Message = Union[commands.Command, events.Event]


def handle_event(
    event: events.Event,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork,
):
    for handler in EVENT_HANDLERS[type(event)]:  # (1)
        try:
            logger.debug("handling event %s with handler %s", event, handler)
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling event %s", event)
            continue  # (2)


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork,
):
    for handler in COMMAND_HANDLERS[type(command)]:  # (1)
        try:
            logger.debug("handling event %s with handler %s", command, handler)
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            logger.exception("Exception handling event %s", command)
            raise


def handle(
    message: Message,
    uow: unit_of_work.AbstractUnitOfWork,
):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)  # (2)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)  # (2)
            results.append(cmd_result)
        else:
            raise Exception(f"{message} was not an Event or Command")
    return results


EVENT_HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.Allocated: [
        handlers.publish_allocated_event,
        handlers.add_allocation_to_read_model,
    ],
    events.Deallocated: [
        handlers.remove_allocation_from_read_model,
        handlers.reallocate,
    ],
}

COMMAND_HANDLERS = {
    commands.Allocate: [handlers.allocate],
    commands.CreateBatch: [handlers.add_batch],
    commands.ChangeBatchQuantity: [handlers.change_batch_quantity],
}
