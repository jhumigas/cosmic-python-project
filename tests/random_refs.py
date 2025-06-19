import uuid


def random_sku(name=""):
    return f"sku-{name}-{uuid.uuid4()}"


def random_batchref(name=""):
    return f"batch-{name}-{uuid.uuid4()}"


def random_orderid(name=""):
    return f"order-{name}-{uuid.uuid4()}"
