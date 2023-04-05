import jwt
from models import User, NewsCard
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from tortoise.contrib.pydantic import pydantic_model_creator
from dotenv import dotenv_values

config = dotenv_values(".env") 
env = dict(config.items())
JWT_SECRET = env["JWT_SECRET"]


User_Pydantic = pydantic_model_creator(User, name="User")
News_Pydantic = pydantic_model_creator(NewsCard, name="News")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)
NewsIn_Pydantic = pydantic_model_creator(NewsCard, name="NewsIn", exclude_readonly=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

async def authenticate_user(username: str, password: str,):
    user = await User.get(username=username)
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user

async def get_current_user(token: str=Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password" )
    
    return await User_Pydantic.from_tortoise_orm(user)

