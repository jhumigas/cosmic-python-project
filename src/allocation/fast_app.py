from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocation import config
from allocation import model
from allocation import orm
from allocation import repository
from allocation import services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = FastAPI()


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.get("/")
async def root():
    return {"message": "Yambu World"}


@app.post("/allocate")
async def allocate(orderid: str, sku: str, qty: int):
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = model.OrderLine(orderid, sku, qty)
    try:
        batchref = services.allocate(line, repo, session)
    except (services.InvalidSku, model.OutOfStock) as e:
        return {"message": str(e)}, 400
    return {"batchref": batchref}, 201
