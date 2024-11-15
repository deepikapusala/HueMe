from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/questions")
async def questions():
    return {"questions": [{"id": 1, "question": "How are You?"}, {"id": 2, "question": "Where are You?"}]}