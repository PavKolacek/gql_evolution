import uuid

import pytest
from sqlalchemy.dialects import postgresql

from src.DBDefinitions.seed import _build_collection_upsert, _is_demo_enabled
from src.DBDefinitions.Domain_Collections.CollectionModel import CollectionModel
from src.DBDefinitions.Domain_Collections.CollectionItemModel import CollectionItemModel


def test_explicit_demo_seed_overrides_missing_env(monkeypatch):
    monkeypatch.delenv("DEMODATA", raising=False)
    assert _is_demo_enabled(force_demo=True)
    assert not _is_demo_enabled()
    monkeypatch.setenv("DEMODATA", "True")
    assert _is_demo_enabled()


@pytest.mark.parametrize(
    ("model", "seed_row", "field"),
    [
        (CollectionModel, {"id": str(uuid.uuid4()), "owner_id": str(uuid.uuid4()),
                           "rbacobject_id": str(uuid.uuid4())}, "rbacobject_id"),
        (CollectionItemModel, {"id": str(uuid.uuid4()), "owner_id": str(uuid.uuid4()),
                               "position": 1}, "owner_id"),
    ],
)
def test_collection_upsert_updates_existing_rows(model, seed_row, field):
    stmt = _build_collection_upsert(model, seed_row)
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (id) DO UPDATE SET" in sql
    assert f"{field} = excluded.{field}" in sql


def test_collection_upsert_fails_on_old_user_id():
    with pytest.raises(ValueError, match="unknown seed fields"):
        _build_collection_upsert(
            CollectionModel,
            {"id": str(uuid.uuid4()), "user_id": str(uuid.uuid4())},
        )
