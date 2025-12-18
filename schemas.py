from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str
    is_teacher: bool

class UserOut(BaseModel):
    id: int
    email: str
    is_teacher: bool

class SubjectCreate(BaseModel):
    name: str

class AssignmentCreate(BaseModel):
    title: str
    description: str
    subject_id: int

class AnswerCreate(BaseModel):
    content: str
    assignment_id: int

class AnswerGrade(BaseModel):
    grade: int

class CommentCreate(BaseModel):
    content: str
    answer_id: int
    is_teacher: bool  # True если комментарий от учителя

class Notification(BaseModel):
    message: str
    user_id: int
    is_read: bool = False