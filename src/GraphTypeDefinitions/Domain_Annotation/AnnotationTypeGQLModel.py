import datetime
import typing

import strawberry

from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension
from uoishelpers.resolvers import (
    DeleteError,
    InsertError,
    InputModelMixin,
    PageResolver,
    UpdateError,
    VectorResolver,
    createInputs2,
)

from src.GraphTypeDefinitions.ApplicationInfo import ApplicationInfo
from src.GraphTypeDefinitions.BaseGQLModel import BaseGQLModel, IDType

AnnotationGQLModel = typing.Annotated[
    "AnnotationGQLModel",
    strawberry.lazy(".AnnotationGQLModel"),
]
AnnotationInputFilter = typing.Annotated[
    "AnnotationInputFilter",
    strawberry.lazy(".AnnotationGQLModel"),
]


@createInputs2
class AnnotationTypeInputFilter:
    id: IDType
    name: str
    name_en: str


@strawberry.federation.type(
    description="Entity representing a type of Annotation",
    keys=["id"],
)
class AnnotationTypeGQLModel(BaseGQLModel):
    LoaderName = "AnnotationTypeModel"

    name: typing.Optional[str] = strawberry.field(
        default=None,
        description="Annotation type name",
        permission_classes=[OnlyForAuthentized],
    )

    name_en: typing.Optional[str] = strawberry.field(
        default=None,
        description="Annotation type name in English",
        permission_classes=[OnlyForAuthentized],
    )

    annotations: typing.List[AnnotationGQLModel] = strawberry.field(
        description="Annotations using this type",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver[AnnotationGQLModel](
            fkey_field_name="annotation_type_id",
            whereType=AnnotationInputFilter,
        ),
    )


@strawberry.interface(description="Annotation type queries")
class AnnotationTypeQuery:
    annotation_type_by_id: typing.Optional[AnnotationTypeGQLModel] = strawberry.field(
        description="Get an annotation type by ID",
        permission_classes=[OnlyForAuthentized],
        resolver=AnnotationTypeGQLModel.load_with_loader,
    )

    annotation_type_page: typing.List[AnnotationTypeGQLModel] = strawberry.field(
        description="Get a page of annotation types",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AnnotationTypeGQLModel](
            whereType=AnnotationTypeInputFilter,
        ),
    )


@strawberry.input(description="Input type for creating an Annotation type")
class AnnotationTypeInsertGQLModel(InputModelMixin):
    getLoader = AnnotationTypeGQLModel.getLoader

    name: str = strawberry.field(description="Annotation type name")
    name_en: typing.Optional[str] = strawberry.field(
        description="Annotation type name in English",
        default=None,
    )
    id: typing.Optional[IDType] = strawberry.field(
        description="Annotation type ID",
        default=None,
    )

    createdby_id: strawberry.Private[IDType] = None
    rbacobject_id: strawberry.Private[IDType] = None


@strawberry.input(description="Input type for updating an Annotation type")
class AnnotationTypeUpdateGQLModel:
    id: IDType = strawberry.field(description="Annotation type ID")
    lastchange: datetime.datetime = strawberry.field(
        description="Timestamp of the last change",
    )
    name: typing.Optional[str] = strawberry.field(
        description="Annotation type name",
        default=strawberry.UNSET,
    )
    name_en: typing.Optional[str] = strawberry.field(
        description="Annotation type name in English",
        default=strawberry.UNSET,
    )

    changedby_id: strawberry.Private[IDType] = None


@strawberry.input(description="Input type for deleting an Annotation type")
class AnnotationTypeDeleteGQLModel:
    id: IDType = strawberry.field(description="Annotation type ID")
    lastchange: datetime.datetime = strawberry.field(
        description="Timestamp of the last change",
    )


@strawberry.interface(description="Annotation type mutations")
class AnnotationTypeMutation:
    @strawberry.mutation(
        description="Insert an Annotation type",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserRoleProviderExtension[InsertError, AnnotationTypeGQLModel](),
            RbacProviderExtension[InsertError, AnnotationTypeGQLModel](),
        ],
    )
    async def annotation_type_insert(
        self,
        info: ApplicationInfo,
        annotation_type: AnnotationTypeInsertGQLModel,
        rbacobject_id: IDType,
        user_roles: typing.List[dict],
    ) -> typing.Union[
        AnnotationTypeGQLModel,
        InsertError[AnnotationTypeGQLModel],
    ]:
        annotation_type.rbacobject_id = rbacobject_id
        service = info.ServiceCtx.Services.AnnotationTypeService

        return await service.ExecuteServiceMethod(
            service.Create(
                ctx=info.ServiceCtx,
                entity=annotation_type,
            ),
            Error=service.CreateErrorCallback(
                ErrorClass=InsertError[AnnotationTypeGQLModel],
                code="ca518e66-3f5e-44ae-a6a4-8463f3bb557c",
                location="annotation_type_insert",
                _input=annotation_type,
            ),
            OK=AnnotationTypeGQLModel.from_dataclass,
        )

    @strawberry.mutation(
        description="Update an Annotation type",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserRoleProviderExtension[UpdateError, AnnotationTypeGQLModel](),
            RbacProviderExtension[UpdateError, AnnotationTypeGQLModel](),
            LoadDataExtension[UpdateError, AnnotationTypeGQLModel](),
        ],
    )
    async def annotation_type_update(
        self,
        info: ApplicationInfo,
        annotation_type: AnnotationTypeUpdateGQLModel,
        db_row: typing.Any,
        rbacobject_id: IDType,
        user_roles: typing.List[dict],
    ) -> typing.Union[
        AnnotationTypeGQLModel,
        UpdateError[AnnotationTypeGQLModel],
    ]:
        service = info.ServiceCtx.Services.AnnotationTypeService

        return await service.ExecuteServiceMethod(
            service.Update(
                ctx=info.ServiceCtx,
                entity=annotation_type,
            ),
            Error=service.CreateErrorCallback(
                ErrorClass=UpdateError[AnnotationTypeGQLModel],
                code="e50d9104-5a83-46b2-932f-45a912793b44",
                location="annotation_type_update",
                _input=annotation_type,
                _entity=AnnotationTypeGQLModel.from_dataclass(db_row),
            ),
            OK=AnnotationTypeGQLModel.from_dataclass,
        )

    @strawberry.mutation(
        description="Delete an Annotation type",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserRoleProviderExtension[DeleteError, AnnotationTypeGQLModel](),
            RbacProviderExtension[DeleteError, AnnotationTypeGQLModel](),
            LoadDataExtension[DeleteError, AnnotationTypeGQLModel](),
        ],
    )
    async def annotation_type_delete(
        self,
        info: ApplicationInfo,
        annotation_type: AnnotationTypeDeleteGQLModel,
        db_row: typing.Any,
        rbacobject_id: IDType,
        user_roles: typing.List[dict],
    ) -> typing.Optional[DeleteError[AnnotationTypeGQLModel]]:
        service = info.ServiceCtx.Services.AnnotationTypeService

        return await service.ExecuteServiceMethod(
            service.Delete(
                ctx=info.ServiceCtx,
                entity=annotation_type,
            ),
            Error=service.CreateErrorCallback(
                ErrorClass=DeleteError[AnnotationTypeGQLModel],
                code="d701d3ec-2de0-4ea0-8a5e-64f7759b8c71",
                location="annotation_type_delete",
                _input=annotation_type,
                _entity=AnnotationTypeGQLModel.from_dataclass(db_row),
            ),
            OK=lambda result: None,
        )