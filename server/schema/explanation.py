from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKeyConstraint, UniqueConstraint

from server.schema.base import Base


class Explanation(Base):
    __tablename__ = "explanation"
    id = Column(Integer, primary_key=True)
    identifier = Column(Text, nullable=False)
    hash = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    project_id = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("identifier", "hash", "project_id"),
        ForeignKeyConstraint(
            ["project_id"], ["projects.id"]
        ),
    )

    # Relationship to a Project model (assuming it exists)
    project = relationship("Project", back_populates="explanation")
