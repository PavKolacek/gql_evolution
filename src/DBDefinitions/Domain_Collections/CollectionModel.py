import typing
import datetime
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
from typing import Optional

###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#
###########################################################################################################################
class CollectionModel(BaseDBModel):
    __tablename__ = "collections" 


    name: Mapped[str] = mapped_column(default=None, nullable=True)
    description: Mapped[str] = mapped_column(default=None, nullable=True)
    user_id: Mapped[Optional[IDType]] = UUIDFKey(ForeignKey("users.id"), default=None, nullable=True)
    color: Mapped[str] = mapped_column(default=None, nullable=True)
    
    items: Mapped[list["CollectionItemModel"]] = relationship(
        "CollectionItemModel",
        order_by="CollectionItemModel.position",
        back_populates="collection",
        uselist=True,
        init=True,
        default_factory=list,
        cascade="save-update",
    )

   