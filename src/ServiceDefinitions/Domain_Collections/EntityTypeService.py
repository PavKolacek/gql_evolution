from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import EntityTypeModel
from src.ServiceDefinitions.BaseService import BaseService, ServiceExceptionWithCode
from src.ServiceDefinitions.ServiceContext import ServiceContext
from . import errors


class EntityTypeService(BaseService[IDLoader[EntityTypeModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[EntityTypeModel]:
        return ctx.loaders.EntityTypeModel

    @classmethod
    async def EnsureExists(cls, ctx, type_id):
        entity_type = await cls.ReadById(ctx, type_id)
        if entity_type is None:
            raise ServiceExceptionWithCode(
                "Entity type not found", code=errors.ENTITY_TYPE_NOT_FOUND, location="EnsureExists"
            )
        return entity_type

    @classmethod
    async def GetChildren(cls, ctx, type_id):
        loader = await cls.getLoader(ctx)
        return await loader.filter_by(parent_id=type_id)

    @classmethod
    async def EnsureNoCycle(cls, ctx, type_id, new_parent_id):
        """Jdeme od nového rodiče nahoru; narazíme-li na type_id, vznikl by cyklus."""
        loader = await cls.getLoader(ctx)
        current = new_parent_id
        visited = set()
        while current is not None:
            if current == type_id or current in visited:
                raise ServiceExceptionWithCode(
                    "Parent change would create a cycle",
                    code=errors.ENTITY_TYPE_CYCLE,
                    location="EnsureNoCycle",
                )
            visited.add(current)
            row = await loader.load(current)
            current = getattr(row, "parent_id", None) if row is not None else None

    @classmethod
    async def UpdateType(cls, ctx, entity):
        """Update s kontrolou cyklu, pokud se mění rodič."""
        new_parent_id = getattr(entity, "parent_id", None)
        if new_parent_id is not None:
            await cls.EnsureNoCycle(ctx, entity.id, new_parent_id)
        return await cls.Update(ctx, entity)

    @classmethod
    async def DeleteType(cls, ctx, entity):
        """Delete jen pokud typ nemá potomky a není použit v položkách."""
        if await cls.GetChildren(ctx, entity.id):
            raise ServiceExceptionWithCode(
                "Entity type has children", code=errors.ENTITY_TYPE_IN_USE, location="DeleteType"
            )
        items = await ctx.loaders.CollectionItemModel.filter_by(entity_type_id=entity.id)
        if items:
            raise ServiceExceptionWithCode(
                "Entity type is used by collection items",
                code=errors.ENTITY_TYPE_IN_USE,
                location="DeleteType",
            )
        return await cls.Delete(ctx, entity)