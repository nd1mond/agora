import shutil
import os
import uuid
import bcrypt
import random  # Для генерации кода
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

# Импорт твоих файлов
from database import get_db, engine
import models

# 1. Создаем таблицы (если удалил их в pgAdmin, они создадутся заново)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 2. Настройки папок
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# ==========================================
# 📧 НАСТРОЙКИ ПОЧТЫ (ВСТАВЬ СВОИ ДАННЫЕ!)
# ==========================================
# Если используешь Яндекс: smtp.yandex.ru, порт 465
# Если Gmail: smtp.gmail.com, порт 465
# ОБЯЗАТЕЛЬНО: Пароль приложения (App Password), а не обычный пароль!

conf = ConnectionConfig(
    MAIL_USERNAME="za1tsef@yandex.ru",  # <--- ВПИШИ СЮДА ПОЧТУ
    MAIL_PASSWORD="bgzosjdmskgpyxjx",  # <--- ВПИШИ СЮДА ПАРОЛЬ ПРИЛОЖЕНИЯ
    MAIL_FROM="za1tsef@yandex.ru",  # <--- ВПИШИ СЮДА ПОЧТУ ЕЩЕ РАЗ
    MAIL_PORT=465,
    MAIL_SERVER="smtp.yandex.ru",  # Или smtp.gmail.com
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

html_email_template = """
<!DOCTYPE html>
<html>
    <body style="background-color: #f3f4f6; padding: 40px; font-family: sans-serif;">
        <div style="max-width: 500px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
            <h1 style="color: #007EC6; margin-bottom: 10px;">Agora.</h1>
            <p style="color: #6b7280; font-size: 16px;">Ваш код подтверждения:</p>
            <div style="background-color: #eff6ff; color: #1d4ed8; font-size: 36px; letter-spacing: 5px; font-weight: bold; padding: 20px; border-radius: 10px; margin: 20px 0;">
                {code}
            </div>
            <p style="color: #9ca3af; font-size: 12px;">Если вы не регистрировались, просто удалите это письмо.</p>
        </div>
    </body>
</html>
"""


# ==========================================
# 🔐 ПАРОЛИ И БЕЗОПАСНОСТЬ
# ==========================================
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


# Функция отправки письма (Асинхронная)
async def send_verification_email(email: str, code: str):
    message = MessageSchema(
        subject="Код подтверждения Agora",
        recipients=[email],
        body=html_email_template.format(code=code),
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message)


# ==========================================
# 🚦 МАРШРУТЫ (ROUTES)
# ==========================================

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 1. РЕГИСТРАЦИЯ -> ОТПРАВКА КОДА
@app.post("/register")
async def register_user(
        background_tasks: BackgroundTasks,  # Чтобы сайт не тормозил пока отправляется письмо
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    # Проверка email
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Этот Email уже зарегистрирован")

    # Генерируем код 1000-9999
    code = str(random.randint(1000, 9999))
    hashed_pw = get_password_hash(password)

    # Создаем НЕАКТИВНОГО пользователя
    new_user = models.User(
        username=name,
        email=email,
        password_hash=hashed_pw,
        verification_code=code,
        is_active=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Отправляем письмо в фоне (чтобы пользователь не ждал)
    try:
        background_tasks.add_task(send_verification_email, email, code)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

    # Перекидываем на страницу ввода кода
    return RedirectResponse(url=f"/verify_page?email={email}", status_code=303)


# 2. СТРАНИЦА ВВОДА КОДА
@app.get("/verify_page")
def verify_page_view(request: Request, email: str):
    return templates.TemplateResponse("verify.html", {"request": request, "email": email})


# 3. ПРОВЕРКА КОДА
@app.post("/verify")
def verify_code_action(
        email: str = Form(...),
        code: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        return RedirectResponse(url="/", status_code=303)  # Если юзера нет - на главную

    if user.verification_code == code:
        # Успех! Активируем
        user.is_active = True
        user.verification_code = None
        db.commit()
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        # Ошибка
        return templates.TemplateResponse("verify.html", {
            "request": {}, "email": email, "error": "Неверный код! Попробуйте еще раз."
        })


# 4. ВХОД (LOGIN)
@app.post("/login")
def login_user(
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()

    # Проверяем пароль
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    # Проверяем, подтвердил ли он почту!
    if not user.is_active:
        # Если не подтвердил - кидаем снова на ввод кода
        return RedirectResponse(url=f"/verify_page?email={email}", status_code=303)

    return RedirectResponse(url="/dashboard", status_code=303)


# 5. ЛИЧНЫЙ КАБИНЕТ
@app.get("/dashboard")
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    files = db.query(models.Material).all()
    user_info = {"username": "Студент", "email": "test@mai.ru", "letter": "S"}  # Заглушка

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "files": files,
        "user": user_info
    })


# 6. ЗАГРУЗКА ФАЙЛОВ
@app.post("/upload")
def upload_material(
        title: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"uploads/{unique_filename}"
    with open(file_path, "wb+") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_material = models.Material(
        title=title, file_path=unique_filename, category_id=1, author_id=1,
        file_type=file.filename.split('.')[-1]
    )
    db.add(new_material)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)