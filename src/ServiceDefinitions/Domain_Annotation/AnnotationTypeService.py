from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import AnnotationTypeModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class AnnotationTypeService(BaseService[IDLoader[AnnotationTypeModel]]):
    @classmethod
    async def getLoader(
        cls,
        ctx: ServiceContext,
    ) -> IDLoader[AnnotationTypeModel]:
        return ctx.loaders.AnnotationTypeModel