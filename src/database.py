import os

from dotenv import load_dotenv
import sqlalchemy

load_dotenv()

DATABASE_URL = os.environ["POSTGRES_URI"]

engine = sqlalchemy.create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)