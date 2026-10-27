import strawberry
from src.GraphTypeDefinitions.Domain_Events import Mutation_Domain_Events
from src.GraphTypeDefinitions.Domain_Annotation import Mutation_Annotation

@strawberry.type(description='Root mutation')
class Mutation(Mutation_Domain_Events, Mutation_Annotation):
    pass
