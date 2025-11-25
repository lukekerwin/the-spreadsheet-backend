from app.models.users import User
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi import Depends
from app.database.session import get_db


async def get_user_db(session=Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)
