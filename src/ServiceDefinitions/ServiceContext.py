import dataclasses
import typing

from src.Dataloaders import LoaderMap

if typing.TYPE_CHECKING:
    from src.ServiceDefinitions.Domain_Annotation.AnnotationService import AnnotationService as _AnnotationService
    from src.ServiceDefinitions.Domain_Collections.EntityTypeService import EntityTypeService as _EntityTypeService
    from src.ServiceDefinitions.Domain_Collections.CollectionService import CollectionService as _CollectionService
    from src.ServiceDefinitions.Domain_Collections.CollectionItemService import CollectionItemService as _CollectionItemService
    from src.ServiceDefinitions.Domain_Events.EventService import EventService as _EventService
    from src.ServiceDefinitions.Domain_Events.EventInvitationService import EventInvitationService as _EventInvitationService
    from src.ServiceDefinitions.Domain_Annotation.AnnotationTypeService import AnnotationTypeService as _AnnotationTypeService

@dataclasses.dataclass(frozen=True)
class ServiceRegistry:
    @property
    def AnnotationService(self) -> type['_AnnotationService']:
        from src.ServiceDefinitions.Domain_Annotation.AnnotationService import AnnotationService
        return AnnotationService


    @property
    def EventInvitationService(self) -> type['_EventInvitationService']:
        from src.ServiceDefinitions.Domain_Events.EventInvitationService import EventInvitationService
        return EventInvitationService

    @property
    def EntityTypeService(self) -> type['_EntityTypeService']:
        from src.ServiceDefinitions.Domain_Collections.EntityTypeService import EntityTypeService
        return EntityTypeService

    @property
    def CollectionService(self) -> type['_CollectionService']:
        from src.ServiceDefinitions.Domain_Collections.CollectionService import CollectionService
        return CollectionService

    @property
    def CollectionItemService(self) -> type['_CollectionItemService']:
        from src.ServiceDefinitions.Domain_Collections.CollectionItemService import CollectionItemService
        return CollectionItemService
    
    @property
    def AnnotationTypeService(self) -> type['_AnnotationTypeService']:
        from src.ServiceDefinitions.Domain_Annotation.AnnotationTypeService import AnnotationTypeService
        return AnnotationTypeService



SERVICES = ServiceRegistry()


@dataclasses.dataclass
class ServiceContext:
    loaders: LoaderMap
    user: typing.Any = None
    ug_client: typing.Callable[..., typing.Awaitable[typing.Any]] | None = None
    request: typing.Any = None
    session: typing.Any = None
    Services: ServiceRegistry = SERVICES

    # uoishelpers helpers commonly expect info.context to behave like a dict
    # with at least the key "loaders". Keeping these methods lets us pass a
    # typed ServiceContext directly as Strawberry context.
    def __getitem__(self, key: str) -> typing.Any:
        return getattr(self, key)

    def get(self, key: str, default: typing.Any = None) -> typing.Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)
