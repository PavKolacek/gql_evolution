
import pytest

from sqlalchemy import ForeignKey, inspect, select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
    Mapped,
    mapped_column,
    relationship,
)

from uoishelpers.dataloaders.IDLoader import detach_entity


class TestBase(MappedAsDataclass, DeclarativeBase):
    pass


class CacheParent(TestBase):
    __tablename__ = "test_cache_parents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        init=False,
    )
    name: Mapped[str]


class CacheChild(TestBase):
    __tablename__ = "test_cache_children"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        init=False,
    )
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("test_cache_parents.id"),
    )
    parent: Mapped[CacheParent] = relationship(
        init=False,
        lazy="select",
    )


@pytest.mark.asyncio
async def test_detach_entity_does_not_lazy_load_relationship():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    try:
        async with engine.begin() as connection:
            await connection.run_sync(TestBase.metadata.create_all)

        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            parent = CacheParent(name="Test parent")
            session.add(parent)
            await session.flush()

            parent_id = parent.id
            session.add(CacheChild(parent_id=parent_id))
            await session.commit()

        async with session_factory() as session:
            child = (
                await session.scalars(select(CacheChild))
            ).one()

            assert "parent" in inspect(child).unloaded

            snapshot = detach_entity(child)

            assert snapshot["parent_id"] == parent_id
            assert "parent" in inspect(child).unloaded

    finally:
        await engine.dispose()

def test_collection_item_snapshot_roundtrip():
    import uuid

    from src.DBDefinitions import CollectionItemModel
    from src.Dataloaders.cache_snapshot import snapshot_entity

    original = CollectionItemModel(
        id=uuid.uuid4(),
        collection_id=uuid.uuid4(),
        entity_id=uuid.uuid4(),
        entity_type_id=uuid.uuid4(),
        position=3,
    )

    snapshot = snapshot_entity(original)
    restored = CollectionItemModel(**snapshot)

    assert restored.id == original.id
    assert restored.collection_id == original.collection_id
    assert restored.entity_id == original.entity_id
    assert restored.entity_type_id == original.entity_type_id
    assert restored.position == original.position

    assert "collection" not in snapshot
    assert "entity_type" not in snapshot



@pytest.mark.asyncio
async def test_collection_item_idloader_cache_hit():
    import uuid
    from types import SimpleNamespace

    from uoishelpers.dataloaders.IDLoader import (
        IDLoader,
        GlobalTTLCache,
        make_entity_cache_key,
    )

    from src.DBDefinitions import CollectionItemModel
    from src.Dataloaders.cache_snapshot import snapshot_entity

    original = CollectionItemModel(
        id=uuid.uuid4(),
        collection_id=uuid.uuid4(),
        entity_id=uuid.uuid4(),
        entity_type_id=uuid.uuid4(),
        position=3,
    )

    cache = GlobalTTLCache(ttl=60.0)
    cache_key = make_entity_cache_key(
        CollectionItemModel,
        original.id,
    )

    await cache.set_many({
        cache_key: snapshot_entity(original)
    })

    # Session bez databázového připojení.
    # Pokud cache nebude fungovat, test selže.
    session = SimpleNamespace(identity_map={})

    loader = IDLoader[CollectionItemModel](
        session=session,
        shared_cache=cache,
    )

    restored = await loader.load(original.id)

    assert restored is not None
    assert isinstance(restored, CollectionItemModel)
    assert restored.id == original.id
    assert restored.collection_id == original.collection_id
    assert restored.entity_id == original.entity_id
    assert restored.entity_type_id == original.entity_type_id
    assert restored.position == original.position
