from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKeyConstraint, PrimaryKeyConstraint

from server.schema.base import Base


class Endpoint(Base):
    __tablename__ = "endpoints"
    path = Column(Text)
    identifier = Column(Text)
    test_plan = Column(Text)
    preferences = Column(Text)
    project_id = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "identifier"),
        ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
    )

    # Relationship to a Project model (assuming it exists)
    project = relationship("Project", back_populates="endpoints")
