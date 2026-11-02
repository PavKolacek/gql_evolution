from sqlalchemy import ForeignKey
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.DBDefinitions.BaseModel import BaseDBModel, IDType


__all__ = [
    "EntityTypeModel",
]


class EntityTypeModel(BaseDBModel):
    """Číselník typů entit, které lze vložit do kolekce (strom typů)."""
    __tablename__ = "entity_types"
    path_attribute_name = "path"
    parent_attribute_name = "parent"
    parent_id_attribute_name = "parent_id"
    children_attribute_name = "children"

    path: Mapped[Optional[str]] = mapped_column(index=True, nullable=True, default=None, comment="Materialized path, not implemented",)
    name: Mapped[Optional[str]] = mapped_column(nullable=True, default=None, comment="např. Projekt, Dokument",)
    name_en: Mapped[Optional[str]] = mapped_column(nullable=True, default=None, comment="e.g. Project, Document",)

    parent_id: Mapped[Optional[IDType]] = mapped_column(ForeignKey("entity_types.id"), index=True, nullable=True, default=None, comment="nadřazený typ ve stromu typů",)
    parent: Mapped[Optional["EntityTypeModel"]] = relationship(
        "EntityTypeModel",
        back_populates="children",
        remote_side="EntityTypeModel.id",
        uselist=False,
        init=False,
    )
    children: Mapped[list["EntityTypeModel"]] = relationship(
        "EntityTypeModel",
        back_populates="parent",
        uselist=True,
        default_factory=list,
        cascade="save-update",
    )
    items: Mapped[list["CollectionItemModel"]] = relationship(
        "CollectionItemModel",
        back_populates="entity_type",
        default_factory=list,
    )