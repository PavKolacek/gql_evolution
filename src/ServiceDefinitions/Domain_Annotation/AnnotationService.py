from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import AnnotationModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class AnnotationService(BaseService[IDLoader[AnnotationModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[AnnotationModel]:
        return ctx.loaders.AnnotationModel