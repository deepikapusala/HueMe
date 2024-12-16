from typing import Annotated
import csv
from fastapi import FastAPI, Depends
from fastapi import Request
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path


app = FastAPI()
app.mount('/app/static', StaticFiles(directory=Path(__file__).parent.parent.absolute() /
          "hueme/app/static", html=True), name='static')


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


def upload_choices():
    with open("app/data/choices.csv", mode="r") as file:
        data = csv.DictReader(file)
        with Session(engine) as session:
            for row in data:
                new_choice = Choice(
                    id=int(row["id"]),
                    question_id=int(row["question_id"]),
                    choice=row["choice"],
                    color_palette=row["color_palette"],
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


class Choice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    choice: str = Field(index=False)
    color_palette: str = Field(default="", index=False)
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
    question_dicts = [question.dict(exclude={"question_id"}) | {
        "choices": question.choices} for question in questions]

    return question_dicts


templates = Jinja2Templates(directory="app/templates")


@app.get("/questions/{id}")
def render_a_question(id, request: Request, session: SessionDep):
    result = session.exec(select(Question).filter(Question.id == id)).first()
    q = result
    result = session.exec(select(Choice).filter(
        Choice.question_id == id)).all()
    c = result
    return templates.TemplateResponse("question.html", {"request": request, "question": q.question, "choices": c, "current_page": int(id), "previous_page": int(id)-1, "next_page": int(id)+1})


@app.get("/questions_in_html")
def get_questions(request: Request, session: SessionDep) -> list[Question]:
    questions = session.exec(select(Question).offset(0).limit(100)).all()
    return templates.TemplateResponse("questions.html", {"request": request, "questions": questions})


@app.post("/evaluate")
async def evaluate_form(request: Request, session: SessionDep):
    form_data = await request.form()
    user_color_palette = dict()
    for data in form_data.items():
        print(data, data[0], data[1])
        id = data[1]
        result_choice = session.exec(
            select(Choice).filter(Choice.id == id)).first()
        color_palette = result_choice.color_palette
        if color_palette in user_color_palette:
            user_color_palette[color_palette] += 1
        else:
            user_color_palette[color_palette] = 1

    max_color_palette = max(user_color_palette, key=user_color_palette.get)
    result = f'You belong to {max_color_palette} seasonal color palette'
    return templates.TemplateResponse("result.html", {"request": request, "result": result})


@app.get("/")
def get_questions(request: Request, session: SessionDep) -> list[Question]:
    questions = session.exec(select(Question).offset(0).limit(100)).all()
    return templates.TemplateResponse("index.html", {"request": request, "questions": questions})


@app.post("/clear_data/{table_name}")
def clear_data_in_table(table_name: str, request: Request, session: SessionDep):

    try:
        query = f"DELETE FROM {table_name}"
        session.exec(query)
        session.commit()
        return templates.TemplateResponse("clear_data.html", {
            "request": request,
            "message": f"Successfully cleared data from {table_name}."
        })
    except Exception as e:
        return templates.TemplateResponse("clear_data.html", {
            "request": request,
            "error": f"Failed to clear data in {table_name}. Error: {str(e)}"
        })
