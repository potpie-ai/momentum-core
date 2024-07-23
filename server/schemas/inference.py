from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from server.schemas.base import Base

class Inference(Base):
    __tablename__ = "inference"
    key = Column(Text, primary_key=True)
    inference = Column(Text)
    hash = Column(Text)
    explanation = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, primary_key=True)

    project = relationship("Project", back_populates="inferences")