from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.DBDefinitions.BaseModel import BaseDBModel

class AnnotationTypeModel(BaseDBModel):
    __tablename__ = "annotationtypes"

    name: Mapped[str] = mapped_column(
        String,
        kw_only=True,
        nullable=False,
        comment="Název typu anotace",
    )
    name_en: Mapped[str | None] = mapped_column(
        String,
        kw_only=True,
        nullable=True,
        default=None,
        comment="Anglický název typu anotace",
    )

    annotations = relationship(
        "AnnotationModel",
        back_populates="annotation_type",
        uselist=True,
    )