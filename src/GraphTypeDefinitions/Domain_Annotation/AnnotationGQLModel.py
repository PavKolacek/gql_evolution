
import datetime
import typing

import strawberry

from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension

from uoishelpers.resolvers import (
    DeleteError,
    InsertError,
    InputModelMixin,
    PageResolver,
    ScalarResolver,
    UpdateError,
    createInputs2,
)

from src.GraphTypeDefinitions.ApplicationInfo import ApplicationInfo
from src.GraphTypeDefinitions.BaseGQLModel import BaseGQLModel, IDType

AnnotationTypeGQLModel = typing.Annotated[
    "AnnotationTypeGQLModel",
    strawberry.lazy(".AnnotationTypeGQLModel"),
]

@createInputs2
class AnnotationInputFilter:
    entity_id: IDType
    entity_type_id: IDType
    annotation_type_id: IDType
    title: str
    owner_id: IDType
    content: str
    id: IDType


@strawberry.federation.type(
    description="Entity representing an Annotation",
    keys=["id"],
)
class AnnotationGQLModel(BaseGQLModel):
    LoaderName = "AnnotationModel"

    entity_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="ID of the annotated entity",
        permission_classes=[OnlyForAuthentized],
    )

    entity_type_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="Type of the annotated entity",
        permission_classes=[OnlyForAuthentized],
    )

    annotation_type_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="ID of the annotation type",
        permission_classes=[OnlyForAuthentized],
    )

    annotation_type: typing.Optional[AnnotationTypeGQLModel] = strawberry.field(
        description="Type of the annotation",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver[AnnotationTypeGQLModel](
            fkey_field_name="annotation_type_id",
        ),
    )

    title: typing.Optional[str] = strawberry.field(
        default=None,
        description="Annotation title",
        permission_classes=[OnlyForAuthentized],
    )

    owner_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="Annotation owner ID",
        permission_classes=[OnlyForAuthentized],
    )

    content: typing.Optional[str] = strawberry.field(
        default=None,
        description="Annotation text content",
        permission_classes=[OnlyForAuthentized],
    )


@strawberry.interface(description="Annotation queries")
class AnnotationQuery:
    annotation_by_id: typing.Optional[AnnotationGQLModel] = strawberry.field(
        description="Get an annotation by ID",
        permission_classes=[OnlyForAuthentized],
        resolver=AnnotationGQLModel.load_with_loader,
    )

    annotation_page: typing.List[AnnotationGQLModel] = strawberry.field(
        description="Get a page of annotations",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AnnotationGQLModel](
            whereType=AnnotationInputFilter
        ),
    )


@strawberry.input(description="Input type for creating an Annotation")
class AnnotationInsertGQLModel(InputModelMixin):
    getLoader = AnnotationGQLModel.getLoader

    entity_id: IDType = strawberry.field(
        description="ID of the annotated entity"
    )

    entity_type_id: IDType = strawberry.field(
        description="Type of the annotated entity"
    )

    annotation_type_id: typing.Optional[IDType] = strawberry.field(
        description="ID of the annotation type",
        default=None,
    )

    title: str = strawberry.field(
        description="Annotation title"
    )

    owner_id: IDType = strawberry.field(
        description="Annotation owner ID"
    )

    content: str = strawberry.field(
        description="Annotation text content"
    )

    id: typing.Optional[IDType] = strawberry.field(
        description="Annotation ID",
        default=None,
    )

    createdby_id: strawberry.Private[IDType] = None
    rbacobject_id: strawberry.Private[IDType] = None


@strawberry.input(description="Input type for updating an Annotation")
class AnnotationUpdateGQLModel:
    id: IDType = strawberry.field(
        description="Annotation ID"
    )

    lastchange: datetime.datetime = strawberry.field(
        description="Timestamp of the last change"
    )

    title: typing.Optional[str] = strawberry.field(
        description="Annotation title",
        default=strawberry.UNSET,
    )

    content: typing.Optional[str] = strawberry.field(
        description="Annotation text content",
        default=strawberry.UNSET,
    )

    annotation_type_id: typing.Optional[IDType] = strawberry.field(
        description="ID of the annotation type",
        default=strawberry.UNSET,
    )

    changedby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Input type for deleting an Annotation")
class AnnotationDeleteGQLModel:
    id: IDType = strawberry.field(
        description="Annotation ID"
    )

    lastchange: datetime.datetime = strawberry.field(
        description="Timestamp of the last change"
    )


@strawberry.interface(description="Annotation mutations")
class AnnotationMutation:

    @strawberry.mutation(
        description="Insert an Annotation",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserRoleProviderExtension[InsertError, AnnotationGQLModel](),
            RbacProviderExtension[InsertError, AnnotationGQLModel](),
        ],
    )
    async def annotation_insert(
        self,
        info: ApplicationInfo,
        annotation: AnnotationInsertGQLModel,
        rbacobject_id: IDType,
        user_roles: typing.List[dict],
    ) -> typing.Union[
        AnnotationGQLModel,
        InsertError[AnnotationGQLModel],
    ]:
        annotation.rbacobject_id = rbacobject_id

        service = info.ServiceCtx.Services.AnnotationService

        return await service.ExecuteServiceMethod(
            service.Create(
                ctx=info.ServiceCtx,
                entity=annotation,
            ),
            Error=service.CreateErrorCallback(
                ErrorClass=InsertError[AnnotationGQLModel],
                code="bb260afb-e7bd-4ed8-89a5-a30bfa2fe6b9",
                location="annotation_insert",
                _input=annotation,
            ),
            OK=AnnotationGQLModel.from_dataclass,
        )

    @strawberry.mutation(
        description="Update an Annotation",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserRoleProviderExtension[UpdateError, AnnotationGQLModel](),
            RbacProviderExtension[UpdateError, AnnotationGQLModel](),
            LoadDataExtension[UpdateError, AnnotationGQLModel](),
        ],
    )
    async def annotation_update(
        self,
        info: ApplicationInfo,
        annotation: AnnotationUpdateGQLModel,
        db_row: typing.Any,
        rbacobject_id: IDType,
        user_roles: typing.List[dict],
    ) -> typing.Union[
        AnnotationGQLModel,
        UpdateError[AnnotationGQLModel],
    ]:
        service = info.ServiceCtx.Services.AnnotationService

        return await service.ExecuteServiceMethod(
            service.Update(
                ctx=info.ServiceCtx,
                entity=annotation,
            ),
            Error=service.CreateErrorCallback(
                ErrorClass=UpdateError[AnnotationGQLModel],
                code="254c14e5-5772-4c6a-b7db-5e06a2246d60",
                location="annotation_update",
                _input=annotation,
                _entity=AnnotationGQLModel.from_dataclass(db_row),
            ),
            OK=AnnotationGQLModel.from_dataclass,
        )

    @strawberry.mutation(
        description="Delete an Annotation",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserRoleProviderExtension[DeleteError, AnnotationGQLModel](),
            RbacProviderExtension[DeleteError, AnnotationGQLModel](),
            LoadDataExtension[DeleteError, AnnotationGQLModel](),
        ],
    )
    async def annotation_delete(
        self,
        info: ApplicationInfo,
        annotation: AnnotationDeleteGQLModel,
        db_row: typing.Any,
        rbacobject_id: IDType,
        user_roles: typing.List[dict],
    ) -> typing.Optional[DeleteError[AnnotationGQLModel]]:
        service = info.ServiceCtx.Services.AnnotationService

        return await service.ExecuteServiceMethod(
            service.Delete(
                ctx=info.ServiceCtx,
                entity=annotation,
            ),
            Error=service.CreateErrorCallback(
                ErrorClass=DeleteError[AnnotationGQLModel],
                code="c09a947c-c33b-416a-99da-06f602571e2d",
                location="annotation_delete",
                _input=annotation,
                _entity=AnnotationGQLModel.from_dataclass(db_row),
            ),
            OK=lambda result: None,
        )
