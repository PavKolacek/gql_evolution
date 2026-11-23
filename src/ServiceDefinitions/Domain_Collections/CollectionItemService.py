import uuid
from sqlalchemy import select
from sqlalchemy import select, update
from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import CollectionItemModel
from src.ServiceDefinitions.BaseService import BaseService, ServiceExceptionWithCode
from src.ServiceDefinitions.ServiceContext import ServiceContext
from . import errors
from .helpers import get_user_id


def _sort_key(item):
    # None pozice patří na konec, aby se po normalizaci „zařadily“ za ostatní
    return (item.position is None, item.position or 0)


class CollectionItemService(BaseService[IDLoader[CollectionItemModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[CollectionItemModel]:
        return ctx.loaders.CollectionItemModel

    # ---------- čtení ----------
    @classmethod
    async def GetOrdered(cls, ctx, collection_id) -> list:
        # Čteme přímo ze session, ne přes FKeyLoader: ten si výsledek pro dané
        # collection_id pamatuje (cache) a po vložení/přesunu by vracel zastaralá data.
        loader = await cls.getLoader(ctx)
        model = loader.getModel()
        statement = (
            select(model)
            .where(model.collection_id == collection_id)
            .execution_options(populate_existing=True)
        )
        rows = (await ctx.session.execute(statement)).scalars().all()
        return sorted(rows, key=_sort_key)

    # ---------- nízkoúrovňový zápis pozice ----------
    @classmethod
    async def _set_position(cls, ctx, row, position: int):
        """Změní jen sloupec position jedné položky (ostatní sloupce zůstanou)."""
        if row.position == position:
            return row
        loader = await cls.getLoader(ctx)
        model = loader.getModel()
        await ctx.session.execute(
            update(model).where(model.id == row.id).values(position=position)
        )
        row.position = position   # drží lokální objekt v souladu s databází
        return row

    @classmethod
    async def _apply_order(cls, ctx, ordered: list):
        """Přečísluje položky na 1..n, zapíše jen ty, které se změnily."""
        for index, row in enumerate(ordered, start=1):
            await cls._set_position(ctx, row, index)

    # ---------- doménové operace ----------
    @classmethod
    async def AddItem(cls, ctx, entity):
        """Přidá položku. position=None => na konec; jinak vloží a posune ostatní."""
        user_id = get_user_id(ctx)
        await ctx.Services.CollectionService.EnsureOwner(ctx, entity.collection_id)

        # --- validace (před jakýmkoli zápisem) ---
        if entity.entity_id is None:
            raise ServiceExceptionWithCode(
                "entity_id is required", code=errors.ITEM_ENTITY_MISSING, location="AddItem"
            )
        await ctx.Services.EntityTypeService.EnsureExists(ctx, entity.entity_type_id)

        items = await cls.GetOrdered(ctx, entity.collection_id)
        if any(i.entity_id == entity.entity_id and i.entity_type_id == entity.entity_type_id for i in items):
            raise ServiceExceptionWithCode(
                "Entity already in collection", code=errors.ITEM_DUPLICATE_ENTITY, location="AddItem"
            )

        target = len(items) + 1 if entity.position is None else entity.position
        if target < 1 or target > len(items) + 1:
            raise ServiceExceptionWithCode(
                "Position out of range", code=errors.ITEM_INVALID_POSITION, location="AddItem"
            )

        # --- zápis ---
        for row in items[target - 1:]:            # posun ostatních o +1
            await cls._set_position(ctx, row, row.position + 1 if row.position else target)
        entity.owner_id = user_id
        entity.position = target
        return await cls.Create(ctx, entity)

    @classmethod
    async def RemoveItem(cls, ctx, entity):
        """Smaže položku a zacelí mezeru v pozicích."""
        item = await cls._load_owned_item(ctx, entity.id)
        items = await cls.GetOrdered(ctx, item.collection_id)
        remaining = [i for i in items if i.id != item.id]
        result = await cls.Delete(ctx, entity)
        await cls._apply_order(ctx, remaining)
        return result

    @classmethod
    async def MoveItem(cls, ctx, entity, new_position: int):
        """Přesune položku na new_position (1..n), ostatní se přeskládají."""
        item = await cls._load_owned_item(ctx, entity.id)
        items = await cls.GetOrdered(ctx, item.collection_id)
        if new_position < 1 or new_position > len(items):
            raise ServiceExceptionWithCode(
                "Position out of range", code=errors.ITEM_INVALID_POSITION, location="MoveItem"
            )
        ordered = [i for i in items if i.id != item.id]
        ordered.insert(new_position - 1, item)
        await cls._apply_order(ctx, ordered)
        return item

    @classmethod
    async def DeleteAllInCollection(cls, ctx, collection_id):
        loader = await cls.getLoader(ctx)
        for row in await loader.filter_by(collection_id=collection_id):
            await loader.delete(row.id)

    # ---------- pomocné ----------
    @classmethod
    async def _load_owned_item(cls, ctx, item_id):
        item = await cls.ReadById(ctx, item_id)
        if item is None:
            raise ServiceExceptionWithCode(
                "Collection item not found", code=errors.ITEM_NOT_FOUND, location="_load_owned_item"
            )
        await ctx.Services.CollectionService.EnsureOwner(ctx, item.collection_id)
        return item