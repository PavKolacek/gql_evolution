
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from src.ServiceDefinitions.Domain_Collections import errors
from src.ServiceDefinitions.Domain_Collections.helpers import get_user_id
from src.ServiceDefinitions.Domain_Collections.EntityTypeService import (
    EntityTypeService,
)


@pytest.fixture
def ctx():
    entity_loader = SimpleNamespace(
        load=AsyncMock(),
        filter_by=AsyncMock(return_value=[]),
    )
    item_loader = SimpleNamespace(
        filter_by=AsyncMock(return_value=[]),
    )
    return SimpleNamespace(
        loaders=SimpleNamespace(
            EntityTypeModel=entity_loader,
            CollectionItemModel=item_loader,
        )
    )


@pytest.mark.asyncio
async def test_ensure_exists_found_and_missing(ctx, monkeypatch):
    entity = SimpleNamespace(id=uuid.uuid4())
    reader = AsyncMock(side_effect=[entity, None])
    monkeypatch.setattr(EntityTypeService, "ReadById", reader)

    assert await EntityTypeService.EnsureExists(ctx, entity.id) is entity

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await EntityTypeService.EnsureExists(ctx, entity.id)

    assert exc.value.code == errors.ENTITY_TYPE_NOT_FOUND


@pytest.mark.asyncio
async def test_get_children(ctx):
    type_id = uuid.uuid4()
    children = [SimpleNamespace(id=uuid.uuid4())]
    loader = ctx.loaders.EntityTypeModel
    loader.filter_by.return_value = children

    result = await EntityTypeService.GetChildren(ctx, type_id)

    assert result == children
    loader.filter_by.assert_awaited_once_with(parent_id=type_id)


@pytest.mark.asyncio
async def test_no_cycle_allows_valid_parent_chain(ctx):
    target = uuid.uuid4()
    parent = uuid.uuid4()
    grandparent = uuid.uuid4()

    rows = {
        parent: SimpleNamespace(parent_id=grandparent),
        grandparent: SimpleNamespace(parent_id=None),
    }
    loader = ctx.loaders.EntityTypeModel
    loader.load.side_effect = lambda key: rows.get(key)

    await EntityTypeService.EnsureNoCycle(ctx, target, parent)

    assert loader.load.await_count == 2


@pytest.mark.asyncio
async def test_no_cycle_rejects_self_reference(ctx):
    target = uuid.uuid4()

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await EntityTypeService.EnsureNoCycle(ctx, target, target)

    assert exc.value.code == errors.ENTITY_TYPE_CYCLE


@pytest.mark.asyncio
async def test_no_cycle_rejects_ancestor_cycle(ctx):
    target = uuid.uuid4()
    parent = uuid.uuid4()

    ctx.loaders.EntityTypeModel.load.return_value = (
        SimpleNamespace(parent_id=target)
    )

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await EntityTypeService.EnsureNoCycle(ctx, target, parent)

    assert exc.value.code == errors.ENTITY_TYPE_CYCLE


@pytest.mark.asyncio
async def test_no_cycle_rejects_existing_loop(ctx):
    target = uuid.uuid4()
    first = uuid.uuid4()
    second = uuid.uuid4()

    rows = {
        first: SimpleNamespace(parent_id=second),
        second: SimpleNamespace(parent_id=first),
    }
    ctx.loaders.EntityTypeModel.load.side_effect = lambda key: rows.get(key)

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await EntityTypeService.EnsureNoCycle(ctx, target, first)

    assert exc.value.code == errors.ENTITY_TYPE_CYCLE


@pytest.mark.asyncio
async def test_update_type_checks_parent(ctx, monkeypatch):
    checker = AsyncMock()
    updater = AsyncMock(return_value="updated")

    monkeypatch.setattr(EntityTypeService, "EnsureNoCycle", checker)
    monkeypatch.setattr(EntityTypeService, "Update", updater)

    entity = SimpleNamespace(
        id=uuid.uuid4(),
        parent_id=uuid.uuid4(),
    )

    assert await EntityTypeService.UpdateType(ctx, entity) == "updated"
    checker.assert_awaited_once_with(
        ctx, entity.id, entity.parent_id
    )

    checker.reset_mock()
    entity.parent_id = None

    await EntityTypeService.UpdateType(ctx, entity)
    checker.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "has_children,has_items",
    [(True, False), (False, True), (False, False)],
)
async def test_delete_type_restrictions(
    ctx, monkeypatch, has_children, has_items
):
    entity = SimpleNamespace(id=uuid.uuid4())

    get_children = AsyncMock(
        return_value=[object()] if has_children else []
    )
    deleter = AsyncMock(return_value=None)

    monkeypatch.setattr(
        EntityTypeService, "GetChildren", get_children
    )
    monkeypatch.setattr(EntityTypeService, "Delete", deleter)

    ctx.loaders.CollectionItemModel.filter_by.return_value = (
        [object()] if has_items else []
    )

    if has_children or has_items:
        with pytest.raises(ServiceExceptionWithCode) as exc:
            await EntityTypeService.DeleteType(ctx, entity)

        assert exc.value.code == errors.ENTITY_TYPE_IN_USE
        deleter.assert_not_awaited()
    else:
        await EntityTypeService.DeleteType(ctx, entity)
        deleter.assert_awaited_once_with(ctx, entity)


def test_get_user_id_dict_and_object():
    user_id = uuid.uuid4()

    assert get_user_id(
        SimpleNamespace(user={"id": str(user_id)})
    ) == user_id

    assert get_user_id(
        SimpleNamespace(user=SimpleNamespace(id=user_id))
    ) == user_id


def test_get_user_id_requires_authentication():
    with pytest.raises(ServiceExceptionWithCode) as exc:
        get_user_id(SimpleNamespace(user=None))

    assert exc.value.code == errors.NOT_AUTHENTICATED
