from passlib.hash import bcrypt
from models import User
from tortoise.contrib.pydantic import pydantic_model_creator

User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)


class UserController():
    def __init__(self):
        pass
    async def create(user):
        user_obj = User(username=user.username, email=user.email, password_hash=bcrypt.hash(user.password_hash), is_superuser=False)
        await user_obj.save()
        return await User_Pydantic.from_tortoise_orm(user_obj)
    
    async def get_one(user):
        return user
