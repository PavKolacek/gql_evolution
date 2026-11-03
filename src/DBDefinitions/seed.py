from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

from uoishelpers.dataloaders import readJsonFile
from uoishelpers.feeders import ImportModels

from src.DBDefinitions import BaseDBModel
from src.DBDefinitions.Domain_Events.EventTypeModel import EventTypeModel


DEFAULT_EVENT_TYPES = (
    {
        'id': uuid.UUID('11111111-1111-1111-1111-111111111111'),
        'name': 'Událost',
        'name_en': 'Event',
    },
    {
        'id': uuid.UUID('22222222-2222-2222-2222-222222222222'),
        'name': 'Schůzka',
        'name_en': 'Meeting',
    },
)

# Pořadí importu podle závislostí cizích klíčů (rodičovské tabulky před dceřinými)
IMPORT_ORDER = [
    # 1. Číselníky a typy
    "tagtypes",
    "entity_types",
    "eventtypes",
    "annotationtypes",
    # 2. Hlavní entity
    "tags",
    "events",
    "collections",
    # 3. Vazební a závislé tabulky
    "tag_entities",
    "event_invitations",
    "annotations",
    "collection_items",
]


def is_sqlalchemy_model(cls: type) -> bool:
    """Return True only for SQLAlchemy mapped model classes."""
    try:
        mapper = sa_inspect(cls, raiseerr=False)
        return mapper is not None
    except NoInspectionAvailable:
        return False


get_demodata = lambda: readJsonFile(jsonFileName="./systemdata.json")


async def init_database_data(session: AsyncSession, get_demodata=get_demodata) -> None:
    """Idempotent seed hook for application startup."""

    json_data = get_demodata()

    # Přetypování ID na UUID
    for annotation_type in json_data.get("annotationtypes", []):
        if annotation_type.get("id") is not None:
            annotation_type["id"] = uuid.UUID(str(annotation_type["id"]))

    for annotation in json_data.get("annotations", []):
        for field in (
            "id",
            "entity_id",
            "entity_type_id",
            "annotation_type_id",
            "owner_id",
        ):
            if annotation.get(field) is not None:
                annotation[field] = uuid.UUID(str(annotation[field]))

    Models = [
        mapper.class_
        for mapper in BaseDBModel.registry.mappers
        if is_sqlalchemy_model(mapper.class_)
    ]

    ModelNames = [Model.__name__ for Model in Models]

    TypeNames = [
        Model.__name__
        for Model in Models
        if Model.__name__.endswith("TypeModel")
    ]

    isDemo = os.environ.get("DEMODATA", None) in ["True", "true", True]

    ModelNamesToImport = ModelNames if isDemo else TypeNames

    print(
        f"Importing models: (isDemo = {isDemo})\n{ModelNamesToImport}",
        flush=True,
    )

    ModelsToImport = [
        Model
        for Model in Models
        if Model.__name__ in ModelNamesToImport
        and is_sqlalchemy_model(Model)
        and hasattr(Model, "__tablename__")
    ]

    # Seřazení podle definovaného pořadí importu
    def get_model_order(model):
        tablename = getattr(model, "__tablename__", "")
        return IMPORT_ORDER.index(tablename) if tablename in IMPORT_ORDER else len(IMPORT_ORDER)

    ModelsToImport = sorted(ModelsToImport, key=get_model_order)

    table_names = [Model.__tablename__ for Model in ModelsToImport]
    modelIndex = dict((DBModel.__tablename__, DBModel) for DBModel in ModelsToImport)
    print(
        f"Models to import: {ModelsToImport}\nTable names: {table_names}\nModel index: {modelIndex}",
        flush=True,
    )

    session_factory_inner = async_sessionmaker(
        session.bind, expire_on_commit=False, class_=AsyncSession
    )

    @asynccontextmanager
    async def session_maker():
        async with session_factory_inner() as s:
            yield s

    await ImportModels(session_maker, ModelsToImport, json_data)

    print("Data initialized", flush=True)


if __name__ == "__main__":
    import asyncio
    from src.DBDefinitions import startEngine, ComposeConnectionString

    async def _main():
        conn_str = ComposeConnectionString()
        session_maker = await startEngine(conn_str, makeUp=True)
        async with session_maker() as session:
            await init_database_data(session)

    asyncio.run(_main())