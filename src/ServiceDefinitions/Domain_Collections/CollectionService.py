from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import CollectionModel
from src.ServiceDefinitions.BaseService import BaseService, ServiceExceptionWithCode
from src.ServiceDefinitions.ServiceContext import ServiceContext
from . import errors
from .helpers import get_user_id


class CollectionService(BaseService[IDLoader[CollectionModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[CollectionModel]:
        return ctx.loaders.CollectionModel

    @classmethod
    async def EnsureOwner(cls, ctx, collection_id) -> CollectionModel:
        """Načte kolekci a ověří, že patří přihlášenému uživateli."""
        collection = await cls.ReadById(ctx, collection_id)
        if collection is None:
            raise ServiceExceptionWithCode(
                "Collection not found", code=errors.COLLECTION_NOT_FOUND, location="EnsureOwner"
            )
        if collection.owner_id != get_user_id(ctx):
            raise ServiceExceptionWithCode(
                "You are not owner of the collection",
                code=errors.COLLECTION_NOT_OWNER,
                location="EnsureOwner",
            )
        return collection

    @classmethod
    async def CreateForUser(cls, ctx, entity):
        """Vlastníkem je vždy přihlášený uživatel, ne hodnota ze vstupu."""
        entity.owner_id = get_user_id(ctx)
        return await cls.Create(ctx, entity)

    @classmethod
    async def UpdateByOwner(cls, ctx, entity):
        await cls.EnsureOwner(ctx, entity.id)
        return await cls.Update(ctx, entity)

    @classmethod
    async def DeleteByOwner(cls, ctx, entity):
        await cls.EnsureOwner(ctx, entity.id)
        # nejdřív položky (FK), potom kolekce
        await ctx.Services.CollectionItemService.DeleteAllInCollection(ctx, entity.id)
        return await cls.Delete(ctx, entity)

    @classmethod
    async def ReadMine(cls, ctx):
        loader = await cls.getLoader(ctx)
        return await loader.filter_by(owner_id=get_user_id(ctx))