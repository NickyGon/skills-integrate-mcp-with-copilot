"""High School Management System API with SQLite persistence using SQLModel."""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine, select
import os

from .models import Activity, Participant


DB_FILE = Path(__file__).parent / "activities.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def seed_data():
    # Seed sample activities if none exist
    with Session(engine) as session:
        count = session.exec(select(Activity)).all()
        if count:
            return

        samples = [
            ("Chess Club", "Learn strategies and compete in chess tournaments", "Fridays, 3:30 PM - 5:00 PM", 12,
             ["michael@mergington.edu", "daniel@mergington.edu"]),
            ("Programming Class", "Learn programming fundamentals and build software projects",
             "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", 20, ["emma@mergington.edu", "sophia@mergington.edu"]),
            ("Gym Class", "Physical education and sports activities", "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
             30, ["john@mergington.edu", "olivia@mergington.edu"]),
            ("Soccer Team", "Join the school soccer team and compete in matches",
             "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", 22, ["liam@mergington.edu", "noah@mergington.edu"]),
            ("Basketball Team", "Practice and play basketball with the school team", "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
             15, ["ava@mergington.edu", "mia@mergington.edu"]),
            ("Art Club", "Explore your creativity through painting and drawing", "Thursdays, 3:30 PM - 5:00 PM",
             15, ["amelia@mergington.edu", "harper@mergington.edu"]),
            ("Drama Club", "Act, direct, and produce plays and performances", "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
             20, ["ella@mergington.edu", "scarlett@mergington.edu"]),
            ("Math Club", "Solve challenging problems and participate in math competitions", "Tuesdays, 3:30 PM - 4:30 PM",
             10, ["james@mergington.edu", "benjamin@mergington.edu"]),
            ("Debate Team", "Develop public speaking and argumentation skills", "Fridays, 4:00 PM - 5:30 PM",
             12, ["charlotte@mergington.edu", "henry@mergington.edu"]),
        ]

        for name, desc, sched, max_p, participants in samples:
            activity = Activity(name=name, description=desc, schedule=sched, max_participants=max_p)
            session.add(activity)
            session.commit()
            session.refresh(activity)
            for email in participants:
                p = Participant(email=email, activity_id=activity.id)
                session.add(p)
            session.commit()


@app.on_event("startup")
def on_startup():
    # Ensure DB directory exists
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    create_db_and_tables()
    seed_data()
    # Mount static files after ensuring path
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with Session(engine) as session:
        activities = session.exec(select(Activity)).all()
        result = {}
        for act in activities:
            participants = session.exec(select(Participant).where(Participant.activity_id == act.id)).all()
            result[act.name] = {
                "description": act.description,
                "schedule": act.schedule,
                "max_participants": act.max_participants,
                "participants": [p.email for p in participants],
            }
        return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        participants = session.exec(select(Participant).where(Participant.activity_id == activity.id)).all()
        if any(p.email == email for p in participants):
            raise HTTPException(status_code=400, detail="Student is already signed up")

        if len(participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        p = Participant(email=email, activity_id=activity.id)
        session.add(p)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        participant = session.exec(
            select(Participant).where(Participant.activity_id == activity.id).where(Participant.email == email)
        ).first()
        if not participant:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(participant)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}
