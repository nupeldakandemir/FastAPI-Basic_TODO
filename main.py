from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
import bcrypt

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    todos = relationship("Todo", back_populates="owner")

class Todo(Base):
    __tablename__ = 'todo'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    task = Column(String)
    is_finished = Column(Boolean, default=False)
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="todos")

# Veritabanı bağlantısı
DATABASE_URL = "URL"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class TodoCreate(BaseModel):
    user_id: int
    task: str
    due_date: datetime

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Şifreyi hash'le
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password.decode('utf-8'))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}

@app.post("/todos/")
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == todo.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_todo = Todo(user_id=todo.user_id, task=todo.task, due_date=todo.due_date)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return {"id": db_todo.id, "task": db_todo.task, "due_date": db_todo.due_date}

@app.get("/todos/{user_id}")
def read_todos(user_id: int, db: Session = Depends(get_db)):
    todos = db.query(Todo).filter(Todo.user_id == user_id).all()
    return todos
