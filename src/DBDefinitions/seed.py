from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
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
    "annotationtypes",
    # 2. Hlavní entity
    "tags",
    "collections",
    # 3. Vazební a závislé tabulky
    "tag_entities",
    "annotations",
    "collection_items",
]


# Tabulky, které seed úplně vynechává (nemaže ani nenahrává).
# Domena Events: ve sdílené DB jsou systémová data UOIS a na events odkazují
# tabulky jiných skupin (event_facility_reservations).
SKIPPED_TABLES = {
    "eventtypes",
    "events",
    "event_invitations",
}


def is_sqlalchemy_model(cls: type) -> bool:
    """Return True only for SQLAlchemy mapped model classes."""
    try:
        mapper = sa_inspect(cls, raiseerr=False)
        return mapper is not None
    except NoInspectionAvailable:
        return False


get_demodata = lambda: readJsonFile(jsonFileName="./systemdata.json")


def get_models_to_import() -> list[type]:
    """Vrátí modely, které seed nahrává, seřazené podle IMPORT_ORDER.

    Při DEMODATA=True všechny modely, jinak jen číselníky (*TypeModel).
    """
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
        and Model.__tablename__ not in SKIPPED_TABLES
    ]

    # Seřazení podle definovaného pořadí importu
    def get_model_order(model):
        tablename = getattr(model, "__tablename__", "")
        return IMPORT_ORDER.index(tablename) if tablename in IMPORT_ORDER else len(IMPORT_ORDER)

    return sorted(ModelsToImport, key=get_model_order)


async def drop_seeded_tables(engine: AsyncEngine, get_demodata=get_demodata) -> list[str]:
    """Smaže (DROP TABLE) tabulky, do kterých seed následně nahraje data.

    Maže se jen tabulka, která se nahrává (viz get_models_to_import) A zároveň pro ni
    existují záznamy v systemdata.json. Tabulky bez dat v JSON (např. events s daty
    systému) zůstanou beze změny.

    Tabulky se po smazání znovu vytvoří přes metadata.create_all, takže odpovídají
    aktuálním modelům (řeší i zastaralé sloupce ve sdílené DB).

    Pokud na mazanou tabulku v databázi odkazuje cizím klíčem jiná tabulka, která se
    nemaže (naše nebo jiné skupiny ve sdílené DB), skončí chybou a nic nesmaže.
    """
    json_data = get_demodata()
    tables = [
        Model.__table__
        for Model in get_models_to_import()
        if json_data.get(Model.__tablename__)
    ]
    names = {table.name for table in tables}

    def _drop(sync_conn):
        inspector = sa_inspect(sync_conn)
        existing = set(inspector.get_table_names())
        blocking = sorted(
            {
                f"{other} -> {fk['referred_table']}"
                for other in existing - names
                for fk in inspector.get_foreign_keys(other)
                if fk["referred_table"] in names
            }
        )
        if blocking:
            raise RuntimeError(
                "Nelze smazat tabulky pro seed, protože na ně odkazují tabulky, "
                f"které se nemažou: {blocking}"
            )
        print(f"Dropping tables before seed: {sorted(names & existing)}", flush=True)
        # drop_all si tabulky sám seřadí podle závislostí (dceřiné před rodičovskými)
        BaseDBModel.metadata.drop_all(sync_conn, tables=tables)

    async with engine.begin() as conn:
        await conn.run_sync(_drop)
    print("Tables dropped", flush=True)
    return sorted(names)


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

    ModelsToImport = get_models_to_import()

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
    from pathlib import Path

    from dotenv import load_dotenv

    from src.DBDefinitions import startEngine, ComposeConnectionString

    # Proměnné (POSTGRES_*, DEMODATA, ...) se berou z environment.txt v kořeni repozitáře,
    # stejně jako při `uvicorn main:app --env-file environment.txt`.
    env_file = Path(__file__).resolve().parents[2] / "environment.txt"
    if not load_dotenv(env_file, override=True):
        raise SystemExit(f"Soubor s proměnnými prostředí nenalezen nebo prázdný: {env_file}")
    print(f"Loaded environment from {env_file}", flush=True)

    async def _main():
        conn_str = ComposeConnectionString()

        # Při ručním spuštění seedu nejdřív smaž tabulky, které se budou nahrávat.
        # (Při startu aplikace přes runtime.py se nic nemaže.)
        engine = create_async_engine(conn_str)
        try:
            await drop_seeded_tables(engine)
        finally:
            await engine.dispose()

        session_maker = await startEngine(conn_str, makeUp=True)
        async with session_maker() as session:
            await init_database_data(session)

    asyncio.run(_main())