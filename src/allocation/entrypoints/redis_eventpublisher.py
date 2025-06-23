from dataclasses import asdict
import json

import redis
from allocation import config
from allocation.domain import events
from allocation.logger import logger


r = redis.Redis(**config.get_redis_host_and_port())


def publish(channel, event: events.Event):  # (1)
    logger.debug("publishing: channel=%s, event=%s", channel, event)
    r.publish(channel, json.dumps(asdict(event)))
