from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException
from allocation.domain import commands, model
from allocation.service_layer import handlers
from allocation import bootstrap
from allocation import views

app = FastAPI()
bus = bootstrap.bootstrap()


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.get("/")
async def root():
    return {"message": "Welcome to the allocation service"}


@app.post("/add_batch", status_code=201)
def add_batch(ref: str, sku: str, qty: int, eta: Optional[date] = None):
    message = commands.CreateBatch(
        ref,
        sku,
        qty,
        eta,
    )
    bus.handle(
        message,
    )
    return "OK"


@app.post("/allocate", status_code=202)
def allocate_endpoint(orderid: str, sku: str, qty: int):
    try:
        message = commands.Allocate(
            orderid,
            sku,
            qty,
        )

        bus.handle(
            message,
        )
    except (model.OutOfStock, handlers.InvalidSku) as e:
        raise HTTPException(status_code=400, detail=str(e))

    return "OK"


@app.get("/allocations/{orderid}", status_code=200)
def allocations_view_endpoint(orderid: str):
    result = views.allocations(orderid, bus.uow)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
