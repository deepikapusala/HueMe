from typing import Annotated

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()

sqlite_file_name = "hueme.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def upload_questions():
    # TODO: Write logic to read CSV data and insert to Table
    pass

def upload_choices():
    # TODO: Write logic to read CSV data and insert to Table
    pass

def upload_data():
    upload_questions()
    upload_choices()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    upload_data()

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@app.get("/")
def read_root():
    return {"message": "Welcome to HueMe!"}

class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question: str = Field(index=False)
    is_enabled: bool | None = Field(default=True, index=False)

class Choice(BaseModel):
    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(index=True)
    choice: str | None = Field(index=False)

@app.post("/questions")
def create_question(question: Question, session: SessionDep) -> Question:
    session.add(question)
    session.commit()
    session.refresh(question)
    return question

@app.get("/questions")
def get_questions(session: SessionDep) -> list[Question]:
    questions = session.exec(select(Question).offset(0).limit(100)).all()
    return questions