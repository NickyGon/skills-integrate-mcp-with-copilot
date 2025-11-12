from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    activity_id: Optional[int] = Field(default=None, foreign_key="activity.id")
    activity: Optional["Activity"] = Relationship(back_populates="participants")


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str
    schedule: str
    max_participants: int
    participants: List[Participant] = Relationship(back_populates="activity")
