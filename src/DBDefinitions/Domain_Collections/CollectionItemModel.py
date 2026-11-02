import typing
import datetime
from typing import Optional
import dataclasses
import sqlalchemy
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, synonym

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, column_property

from src.DBDefinitions.BaseModel import BaseDBModel, UUIDColumn, UUIDFKey, IDType

###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#
###########################################################################################################################
class CollectionItemModel(BaseDBModel):
    __tablename__ = "collection_items" 

    collection_id: Mapped[Optional[IDType]] = mapped_column(ForeignKey("collections.id"), index =True, nullable=True, default=None,)
    collection: Mapped[Optional["CollectionModel"]] = relationship(
        "CollectionModel",
        back_populates="items",
        init=False,
    )
    user_id: Mapped[Optional[IDType]] = UUIDFKey(ForeignKey("users.id"), default=None, nullable=True, comment="User assigned to the invitation")
    entity_id: Mapped[IDType] = mapped_column(default=None, nullable=True)
    entity_type_id: Mapped[Optional[IDType]] = mapped_column(ForeignKey("entity_types.id"), index=True, nullable=True, default=None,)
    entity_type: Mapped[Optional["EntityTypeModel"]] = relationship(
        "EntityTypeModel",
        back_populates="items",
        init=False,
    )
    position: Mapped[int] = mapped_column(default=None, nullable=True)

    __table_args__ = (sqlalchemy.Index("ix_collection_items_entity", "entity_type_id", "entity_id"),)


   