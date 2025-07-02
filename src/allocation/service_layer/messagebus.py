from typing import Callable, Dict, List, Type, Union
from allocation.logger import logger
from allocation.domain import commands, events
from allocation.service_layer import unit_of_work


Message = Union[commands.Command, events.Event]


class MessageBus:
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: Dict[Type[events.Event], List[Callable]],
        command_handlers: Dict[Type[commands.Command], List[Callable]],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: events.Event):
        for handler in self.event_handlers[type(event)]:
            try:
                logger.debug("handling event %s with handler %s", event, handler)
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    def handle_command(self, command: commands.Command):
        logger.debug("handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise


# def handle_event(
#     event: events.Event,
#     queue: List[Message],
#     uow: unit_of_work.AbstractUnitOfWork,
# ):
#     for handler in EVENT_HANDLERS[type(event)]:  # (1)
#         try:
#             logger.debug("handling event %s with handler %s", event, handler)
#             handler(event, uow=uow)
#             queue.extend(uow.collect_new_events())
#         except Exception:
#             logger.exception("Exception handling event %s", event)
#             continue  # (2)


# def handle_command(
#     command: commands.Command,
#     queue: List[Message],
#     uow: unit_of_work.AbstractUnitOfWork,
# ):
#     for handler in COMMAND_HANDLERS[type(command)]:  # (1)
#         try:
#             logger.debug("handling event %s with handler %s", command, handler)
#             result = handler(command, uow=uow)
#             queue.extend(uow.collect_new_events())
#             return result
#         except Exception:
#             logger.exception("Exception handling event %s", command)
#             raise


# def handle(
#     message: Message,
#     uow: unit_of_work.AbstractUnitOfWork,
# ):
#     results = []
#     queue = [message]
#     while queue:
#         message = queue.pop(0)
#         if isinstance(message, events.Event):
#             handle_event(message, queue, uow)  # (2)
#         elif isinstance(message, commands.Command):
#             cmd_result = handle_command(message, queue, uow)  # (2)
#             results.append(cmd_result)
#         else:
#             raise Exception(f"{message} was not an Event or Command")
#     return results


# EVENT_HANDLERS = {
#     events.OutOfStock: [handlers.send_out_of_stock_notification],
#     events.Allocated: [
#         handlers.publish_allocated_event,
#         handlers.add_allocation_to_read_model,
#     ],
#     events.Deallocated: [
#         handlers.remove_allocation_from_read_model,
#         handlers.reallocate,
#     ],
# }

# COMMAND_HANDLERS = {
#     commands.Allocate: [handlers.allocate],
#     commands.CreateBatch: [handlers.add_batch],
#     commands.ChangeBatchQuantity: [handlers.change_batch_quantity],
# }
