from fastapi import FastAPI
from allocation.domain import model
from allocation.adapters import orm
from allocation.service_layer import services
from allocation.service_layer import unit_of_work

orm.start_mappers()
app = FastAPI()


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.get("/")
async def root():
    return {"message": "Yambu World"}


@app.post("/allocate")
async def allocate(orderid: str, sku: str, qty: int):
    try:
        batchref = services.allocate(
            orderid=orderid, sku=sku, qty=qty, uow=unit_of_work.SqlAlchemyUnitOfWork()
        )
    except (services.InvalidSku, model.OutOfStock) as e:
        return {"message": str(e)}, 400
    return {"batchref": batchref}, 201
