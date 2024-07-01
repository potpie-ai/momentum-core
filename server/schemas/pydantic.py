from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, Text
from sqlalchemy.orm import relationship
from server.schemas.base import Base


class Pydantic(Base):
    __tablename__ = 'pydantic'

    filepath = Column(Text)
    classname = Column(Text)
    definition = Column(Text)
    project_id = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(filepath, classname),
        ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
    )

    # Define relationship to the 'projects' table
    project = relationship("Project", back_populates="pydantic")
