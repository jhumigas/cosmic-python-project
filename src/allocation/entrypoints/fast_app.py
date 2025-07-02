from datetime import date
from typing import Optional
from fastapi import FastAPI
from allocation.domain import commands, model
from allocation.service_layer import handlers
from allocation import bootstrap

app = FastAPI()
bus = bootstrap.bootstrap()


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.get("/")
async def root():
    return {"message": "Yambu World"}


@app.post("/add_batch")
def add_batch(ref: str, sku: str, qty: int, eta: Optional[date]):
    event = commands.CreateBatch(
        ref,
        sku,
        qty,
        eta,
    )

    bus.handle(
        event,
    )
    return "OK", 201


@app.post("/allocate")
def allocate_endpoint(orderid: str, sku: str, qty: int):
    try:
        event = commands.Allocate(
            orderid,
            sku,
            qty,
        )

        results = bus.handle(
            event,
        )
        batchref = results.pop(0)
    except (model.OutOfStock, handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201
