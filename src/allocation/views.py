from allocation.service_layer import unit_of_work


def allocations(orderid: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        results = uow.execute(
            """
        SELECT ol.sku, b.reference
        FROM allocations AS a
        JOIN batches AS b ON a.batch_id = b.id
        JOIN order_lines AS ol ON a.orderline_id = ol.id
        WHERE ol.orderid = :orderid
        """,
            dict(orderid=orderid),
        )
        return [{"sku": sku, "batchref": batchref} for sku, batchref in results]
