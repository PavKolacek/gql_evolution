from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader

import src.DBDefinitions
from src.DBDefinitions import BaseDBModel, EventModel, EventInvitationModel


from src.DBDefinitions import (
    BaseDBModel,
    EventModel,
    EventInvitationModel,
    AnnotationModel,
    AnnotationTypeModel,
    TagTypeModel,
    TagModel,
    TagEntityModel,
)

class LoaderMap(LoaderMapBase[BaseDBModel]):
    BaseModel = BaseDBModel

    EventModel: IDLoader[src.DBDefinitions.EventModel] = None
    EventInvitationModel: IDLoader[src.DBDefinitions.EventInvitationModel] = None
    AnnotationModel: IDLoader[src.DBDefinitions.AnnotationModel] = None
    AnnotationTypeModel: IDLoader[src.DBDefinitions.AnnotationTypeModel] = None
    TagTypeModel: IDLoader[src.DBDefinitions.TagTypeModel] = None
    TagModel: IDLoader[src.DBDefinitions.TagModel] = None
    TagEntityModel: IDLoader[src.DBDefinitions.TagEntityModel] = None

    def __init__(self, session):
        super().__init__(session)
        self.EventModel = self.get(EventModel)
        self.EventInvitationModel = self.get(EventInvitationModel)
        
        self.AnnotationModel = self.get(AnnotationModel)
        self.AnnotationTypeModel = self.get(AnnotationTypeModel)
        self.TagTypeModel = self.get(TagTypeModel)
        self.TagModel = self.get(TagModel)
        self.TagEntityModel = self.get(TagEntityModel)
    
    def get_by_name(self, name: str):
        return getattr(self, name)


def createLoadersContext(session):
    """Compatibility helper for places expecting a dict context."""
    return {'loaders': LoaderMap(session)}
