import strawberry

from .AnnotationGQLModel import (
    AnnotationGQLModel,
    AnnotationInputFilter,
    AnnotationMutation,
    AnnotationQuery,
)
from .AnnotationTypeGQLModel import (
    AnnotationTypeGQLModel,
    AnnotationTypeInputFilter,
    AnnotationTypeMutation,
    AnnotationTypeQuery,
)


@strawberry.interface(description='Annotation domain queries')
class Query_Annotation(AnnotationQuery, AnnotationTypeQuery):
    pass


@strawberry.interface(description='Annotation domain mutations')
class Mutation_Annotation(AnnotationMutation, AnnotationTypeMutation):
    pass


__all__ = [
    'AnnotationGQLModel',
    'AnnotationInputFilter',
    'AnnotationTypeGQLModel',
    'AnnotationTypeInputFilter',
    'Query_Annotation',
    'Mutation_Annotation',
]