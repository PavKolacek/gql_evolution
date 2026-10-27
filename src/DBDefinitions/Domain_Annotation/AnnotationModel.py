import typing # pyright: ignore[reportUnusedImport]

import datetime # pyright: ignore[reportUnusedImport]

import dataclasses # pyright: ignore[reportUnusedImport]

import sqlalchemy # pyright: ignore[reportUnusedImport]

from sqlalchemy import (Column, String, Text, DateTime, ForeignKey,) # pyright: ignore[reportUnusedImport]
from typing import Optional


from sqlalchemy.orm import Mapped, mapped_column, synonym # pyright: ignore[reportUnusedImport]

from sqlalchemy.ext.hybrid import hybrid_property # pyright: ignore[reportUnusedImport]

from sqlalchemy.orm import relationship, column_property # pyright: ignore[reportUnusedImport]


from src.DBDefinitions.BaseModel import BaseDBModel, UUIDColumn, UUIDFKey, IDType # pyright: ignore[reportUnusedImport]



class AnnotationModel(BaseDBModel):
    __tablename__ = "annotations"

    # Identifikátor anotované entity
    entity_id: Mapped[IDType] = mapped_column(
        kw_only=True,
        nullable=False,
        index=True,
    )

    # Typ anotované entity
    entity_type_id: Mapped[IDType] = mapped_column(
        kw_only=True,
        nullable=False,
        index=True,
    )

    # Název anotace
    title: Mapped[str] = mapped_column(
        String,
        kw_only=True,
        nullable=False,
    )

    # Vlastník anotace
    owner_id: Mapped[IDType] = mapped_column(
        kw_only=True,
        nullable=False,
        index=True,
    )

    # Typ anotace
    annotation_type_id: Mapped[Optional[IDType]] = mapped_column(
        ForeignKey("annotationtypes.id"),
        kw_only=True,
        nullable=True,
        default=None,
        index=True,
    )

    annotation_type = relationship(
        "AnnotationTypeModel",
        back_populates="annotations",
        uselist=False,
    )

    # Text anotace
    content: Mapped[str] = mapped_column(
        Text,
        kw_only=True,
        nullable=False,
    )