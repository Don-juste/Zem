from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()
import os
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./ma_base.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL=DATABASE_URL.replace("postgres://","postgresqlite://",1)
engine=create_engine(DATABASE_URL)
Base=declarative_base()
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

