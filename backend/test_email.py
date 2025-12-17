import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

# === НАСТРОЙКИ (Впиши свои данные сюда) ===
MY_EMAIL = "za1tsef@yandex.ru"  # Твоя почта
MY_APP_PASSWORD = "bgzosjdmskgpyxjx"  # Твой Пароль приложения (можно с пробелами)

# Настройки для Яндекса
conf = ConnectionConfig(
    MAIL_USERNAME=MY_EMAIL,
    MAIL_PASSWORD=MY_APP_PASSWORD,
    MAIL_FROM=MY_EMAIL,
    MAIL_PORT=465,
    MAIL_SERVER="smtp.yandex.ru",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def test_send():
    print(f"1. Попытка подключения к {conf.MAIL_SERVER}...")

    message = MessageSchema(
        subject="Тест связи Agora",
        recipients=[MY_EMAIL],  # Отправляем самому себе
        body="<h1>Привет! Если ты это читаешь, значит почта работает.</h1>",
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    try:
        await fm.send_message(message)
        print("✅ УСПЕХ! Письмо отправлено. Проверь папку 'Входящие' или 'Спам'.")
    except Exception as e:
        print("\n❌ ОШИБКА ОТПРАВКИ:")
        print(e)


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(test_send())