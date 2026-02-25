import os
from dotenv import load_dotenv

load_dotenv()

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TG_BOT_TOKEN:
    raise RuntimeError("Не задан TG_BOT_TOKEN (см. .env.example)")
if not DATABASE_URL:
    raise RuntimeError("Не задан DATABASE_URL (см. .env.example)")