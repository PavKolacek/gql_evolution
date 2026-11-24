
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.ServiceDefinitions.Domain_Annotation.AnnotationService import AnnotationService
from src.ServiceDefinitions.Domain_Annotation.AnnotationTypeService import AnnotationTypeService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_cls, loader_name",
    [
        (AnnotationService, "AnnotationModel"),
        (AnnotationTypeService, "AnnotationTypeModel"),
    ],
)
async def test_annotation_service_uses_correct_loader(
    service_cls, loader_name
):
    record_id = uuid.uuid4()
    record = SimpleNamespace(id=record_id)

    loader = SimpleNamespace(
        load=AsyncMock(return_value=record)
    )

    ctx = SimpleNamespace(
        loaders=SimpleNamespace(**{loader_name: loader})
    )

    # Ověření správného dataloaderu
    assert await service_cls.getLoader(ctx) is loader

    # Ověření delegování ReadById na dataloader
    result = await service_cls.ReadById(ctx, record_id)

    assert result is record
    loader.load.assert_awaited_once_with(record_id)
    