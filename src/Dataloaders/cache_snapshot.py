
from dataclasses import fields, is_dataclass

from sqlalchemy import inspect
from sqlalchemy.orm.attributes import NO_VALUE


def snapshot_entity(entity):
    """Vytvoří cache snapshot bez implicitního načítání vztahů."""

    if entity is None:
        return None

    if not is_dataclass(entity):
        return entity

    state = inspect(entity)

    # Pouze atributy přijímané konstruktorem dataclass.
    init_fields = {
        field.name
        for field in fields(entity)
        if field.init
    }

    snapshot = {}

    for column in state.mapper.column_attrs:
        name = column.key

        if name not in init_fields:
            continue

        # loaded_value nevyvolává databázový dotaz.
        value = state.attrs[name].loaded_value

        if value is not NO_VALUE:
            snapshot[name] = value

    return snapshot
