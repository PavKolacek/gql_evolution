import types, uuid
import pytest

from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from src.ServiceDefinitions.Domain_Collections import errors
from src.ServiceDefinitions.Domain_Collections.CollectionItemService import CollectionItemService


class FakeItemLoader:
    def __init__(self, items):
        self.items = {i.id: i for i in items}
        self.updated = []

    def getModel(self):
        return types.SimpleNamespace          # model(id=..., lastchange=..., position=...)

    async def load(self, id_):
        return self.items.get(id_)

    async def filter_by(self, **kw):
        return [i for i in self.items.values() if i.collection_id == kw["collection_id"]]

    async def update(self, *, entity, **kw):
        self.updated.append((entity.id, entity.position))
        self.items[entity.id].position = entity.position
        return self.items[entity.id]


def _item(collection_id, position):
    return types.SimpleNamespace(
        id=uuid.uuid4(), collection_id=collection_id, position=position,
        lastchange=None, entity_id=uuid.uuid4(), entity_type_id=uuid.uuid4(),
    )


@pytest.mark.asyncio
async def test_move_item_reorders_and_writes_only_changed_rows(monkeypatch):
    user_id, coll_id = uuid.uuid4(), uuid.uuid4()
    a, b, c = _item(coll_id, 1), _item(coll_id, 2), _item(coll_id, 3)
    loader = FakeItemLoader([a, b, c])

    async def fake_get_loader(cls, ctx):
        return loader
    monkeypatch.setattr(CollectionItemService, "getLoader", classmethod(fake_get_loader))

    class FakeCollectionService:
        @classmethod
        async def EnsureOwner(cls, ctx, collection_id):
            return None
    # ReadById používá loader, takže stačí fake loader
    ctx = types.SimpleNamespace(
        user={"id": str(user_id)},
        Services=types.SimpleNamespace(CollectionService=FakeCollectionService),
    )

    await CollectionItemService.MoveItem(ctx, types.SimpleNamespace(id=c.id), new_position=1)

    assert [i.position for i in (c, a, b)] == [1, 2, 3]
    assert len(loader.updated) == 3          # c->1, a->2, b->3