from typing import Annotated
import csv, json
from fastapi import FastAPI, Depends
from fastapi import Response
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship

app = FastAPI()

sqlite_file_name = "hueme.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)



def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



def upload_questions():
    with open("app/data/questions.csv", mode="r") as file:
        data = csv.DictReader(file)
        with Session(engine) as session:
            for row in data:
                new_question = Question(
                    id=int(row["id"]),
                    question=row["question"],
                    is_enabled=row["is_enabled"].strip().lower() == "true",
                    keywords=row["keywords"]
                )
                session.add(new_question)  
            session.commit()
        
    with open("app/data/questions.csv", mode="r") as file:
        data = csv.DictReader(file)
        with Session(engine) as session:
            for row in data:
                new_question = Question(
                    id=int(row["id"]),
                    question=row["question"],
                    is_enabled=row["is_enabled"].strip().lower() == "true",
                    keywords=row["keywords"]
                )
                session.add(new_question)  
            session.commit()
        

def upload_choices():
    with open("app/data/choices.csv", mode="r") as file:
        data = csv.DictReader(file)
        with Session(engine) as session:
            for row in data:
                new_choice = Choice(
                    id=int(row["id"]),
                    question_id=int(row["question_id"]),
                    choice=row["choice"],
                    description=row["description"]
                )
                session.add(new_choice)  
            session.commit()  

    with open("app/data/choices.csv", mode="r") as file:
        data = csv.DictReader(file)
        with Session(engine) as session:
            for row in data:
                new_choice = Choice(
                    id=int(row["id"]),
                    question_id=int(row["question_id"]),
                    choice=row["choice"],
                    description=row["description"]
                )
                session.add(new_choice)  
            session.commit()  


def upload_data():
    upload_questions()
    upload_choices()



@app.on_event("startup")
def on_startup():
    create_db_and_tables()



def get_session():
    with Session(engine) as session:
        yield session



SessionDep = Annotated[Session, Depends(get_session)]



@app.get("/")
def read_root():
    return {"message": "Welcome to HueMe!"}


class Choice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    choice: str = Field(index=False)
    description: str = Field(default="", index=False)
    question_id: int = Field(foreign_key="question.id", nullable=False)
    question: "Question" = Relationship(back_populates="choices") 


class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question: str = Field(index=False)
    is_enabled: bool | None = Field(default=True, index=False)
    keywords: str = Field(index=False)
    choices: list[Choice] = Relationship(back_populates="question")


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


@app.get("/data/seed")
def seed_data():
    upload_data()
    return {"message": "Success!"}


@app.get("/play")
def play(session: SessionDep):
    questions = session.execute(select(Question)).scalars()
    question_dicts = [question.dict(exclude={"question_id"}) | {"choices": question.choices} for question in questions]

    return question_dicts

