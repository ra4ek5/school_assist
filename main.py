from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


from . import models, schemas, auth
from .database import SessionLocal, engine, Base


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# Регистрация пользователя
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Данная почта уже используется.")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_teacher=user.is_teacher
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Аутентификация
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный логин или пароль.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Создание предмета (только для учителей)
@app.post("/subjects", response_model=schemas.SubjectCreate)
def create_subject(subject: schemas.SubjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_teacher:
        raise HTTPException(status_code=403, detail="Только учителя могут создавать предметы.")
    db_subject = models.Subject(name=subject.name, teacher_id=current_user.id)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

# Создание задания (только для учителей)
@app.post("/assignments", response_model=schemas.AssignmentCreate)
def create_assignment(assignment: schemas.AssignmentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_teacher:
        raise HTTPException(status_code=403, detail="только учителя могут создавать задания.")
    db_assignment = models.Assignment(
        title=assignment.title,
        description=assignment.description,
        subject_id=assignment.subject_id,
        teacher_id=current_user.id
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@app.post("/answers", response_model=schemas.AnswerCreate)
def create_answer(
        answer: schemas.AnswerCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.is_teacher:
        raise HTTPException(status_code=403, detail="Учителя не могут отправлять ответы.")

    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == answer.assignment_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Задание не найдено.")

    db_answer = models.Answer(
        content=answer.content,
        assignment_id=answer.assignment_id,
        student_id=current_user.id
    )

    # Уведомление для учителя
    notification = models.Notification(
        message=f"Новый ответ на задание '{assignment.title}'.",
        user_id=assignment.teacher_id
    )

    db.add(db_answer)
    db.add(notification)
    db.commit()

    return db_answer

# Оценка ответа (только для учителей)
@app.put("/answers/{answer_id}/grade")
def grade_answer(answer_id: int, grade: schemas.AnswerGrade, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_teacher:
        raise HTTPException(status_code=403, detail="Только учителя могут оценивать ответы.")
    db_answer = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if not db_answer:
        raise HTTPException(status_code=404, detail="Такого ответа не существует.")
    db_answer.grade = grade.grade
    db.commit()
    return {"message": "Оценка обновлена."}


# Эндпоинты для комментариев
@app.post("/comments", response_model=schemas.CommentCreate)
def create_comment(
        comment: schemas.CommentCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(auth.get_current_user)
):
    # Проверяем существует ли ответ
    answer = db.query(models.Answer).filter(models.Answer.id == comment.answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Ответ не найден.")

    # Создаем комментарий
    db_comment = models.Comment(
        content=comment.content,
        answer_id=comment.answer_id,
        user_id=current_user.id,
        is_teacher=current_user.is_teacher
    )

    # Создаем уведомление
    recipient_id = answer.student_id if current_user.is_teacher else answer.assignment.teacher_id
    notification_msg = f"Новый комментарий к вашему ответу '{answer.assignment.title}'."

    db_notification = models.Notification(
        message=notification_msg,
        user_id=recipient_id
    )

    db.add(db_comment)
    db.add(db_notification)
    db.commit()

    return db_comment


@app.get("/answers/{answer_id}/comments", response_model=List[schemas.CommentCreate])
def get_comments(
        answer_id: int,
        db: Session = Depends(get_db)
):
    comments = db.query(models.Comment).filter(models.Comment.answer_id == answer_id).all()
    return comments


# Эндпоинты для уведомлений
@app.get("/notifications", response_model=List[schemas.Notification])
def get_notifications(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(auth.get_current_user)
):
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).all()
    return notifications


@app.put("/notifications/{notification_id}/read")
def mark_as_read(
        notification_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(auth.get_current_user)
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено.")

    notification.is_read = True
    db.commit()
    return {"message": "Уведомление отмечено как прочитанное."}