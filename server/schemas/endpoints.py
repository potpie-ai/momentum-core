import logging
from sqlalchemy import Column, Integer, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKeyConstraint, PrimaryKeyConstraint
from server.schemas.base import Base


class Endpoint(Base):
    __tablename__ = "endpoints"
    
    path = Column(Text)
    identifier = Column(Text)
    test_plan = Column(Text)
    preferences = Column(Text)
    configuration = Column(JSON)
    project_id = Column(Integer, nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint("project_id", "identifier"),
        ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
    )
    project = relationship("Project", back_populates="endpoints")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)