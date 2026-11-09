import uuid

import pytest

from src.DBDefinitions import CollectionItemModel, CollectionModel


@pytest.mark.explicit
@pytest.mark.asyncio
async def test_collection_add_move_remove_items_explicit(explicit_service_ctx):
    ctx = explicit_service_ctx
    ctx.user = {"id": str(uuid.uuid4())}
    collections = ctx.Services.CollectionService
    items = ctx.Services.CollectionItemService

    coll = await collections.CreateForUser(ctx, CollectionModel(name="pytest kolekce"))
    type_id = uuid.UUID("5a9d7c31-2e84-4b6f-a1d0-9f3c8e2b6a47")   # Projekt ze systemdata.json

    created = []
    for _ in range(3):
        created.append(await items.AddItem(ctx, CollectionItemModel(
            collection_id=coll.id, entity_id=uuid.uuid4(), entity_type_id=type_id)))

    ordered = await items.GetOrdered(ctx, coll.id)
    assert [i.position for i in ordered] == [1, 2, 3]

    await items.MoveItem(ctx, created[2], new_position=1)
    ordered = await items.GetOrdered(ctx, coll.id)
    assert ordered[0].id == created[2].id
    assert [i.position for i in ordered] == [1, 2, 3]

    await items.RemoveItem(ctx, created[0])
    ordered = await items.GetOrdered(ctx, coll.id)
    assert [i.position for i in ordered] == [1, 2]

    await collections.DeleteByOwner(ctx, CollectionModel(id=coll.id, lastchange=(await collections.ReadById(ctx, coll.id)).lastchange))
    assert await collections.ReadById(ctx, coll.id) is None