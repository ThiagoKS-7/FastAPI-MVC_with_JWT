import jwt
import uvicorn
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from passlib.hash import bcrypt
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from dotenv import dotenv_values
from models import User, NewsCard, Status
from utils.auh_util import authenticate_user, get_current_user
from controllers.user_controller import UserController
from controllers.admin_controller import AdminController
from controllers.news_controller import NewsController

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
]

config = dotenv_values(".env") 
env = dict(config.items())
JWT_SECRET = env["JWT_SECRET"]

router = APIRouter(prefix="/api/v1")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_tortoise(
    app,
    db_url=env["MYSQL_URL"],
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

User_Pydantic = pydantic_model_creator(User, name="User")
News_Pydantic = pydantic_model_creator(NewsCard, name="News")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)
NewsIn_Pydantic = pydantic_model_creator(NewsCard, name="NewsIn", exclude_readonly=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


@app.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials" )
    
    
    user_obj = await User_Pydantic.from_tortoise_orm(user)
    token = jwt.encode({"id": user_obj.id, 
                        "username": user_obj.username, 
                        "email": user_obj.email, 
                        "is_superuser": user_obj.is_superuser
                    }, JWT_SECRET)
    return {
        "status": status.HTTP_200_OK,
        "data": {
            "acess_token": token,
            "token_type": "bearer"
        }
    }

@router.get('/')
async def index():
    return {"hello": "world"}

@router.post("/users/new", response_model=User_Pydantic)
async def create_user(user: UserIn_Pydantic):
    return await UserController.create(user)

@router.post("/admin/new", response_model=User_Pydantic)
async def create_user_admin(user: UserIn_Pydantic, token: str=Depends(oauth2_scheme)):
    return await AdminController.create(user, token)
    
@router.get("/users/me")
async def get_user(user: UserIn_Pydantic=Depends(get_current_user)):
    return await UserController.get_one(user)

@router.post("/news/add", response_model=News_Pydantic)
async def create_newscard( data: NewsIn_Pydantic, token: str=Depends(oauth2_scheme)):
    return await NewsController.create(data,token)

@router.get("/news")
async def get_newscards():
    return await NewsController.get_all()

@router.get("/news/{news_id}", response_model=News_Pydantic, responses={404: {"model": HTTPNotFoundError}})
async def get_newscard(news_id:int):
    return await NewsController.get_one(news_id)

@router.put("/news/{news_id}", response_model=News_Pydantic, responses={404: {"model": HTTPNotFoundError}})
async def get_newscard(news_id:int, news: NewsIn_Pydantic, token: str=Depends(oauth2_scheme)):
   return await NewsController.update(news_id, news, token)
    
@router.delete("/news/{news_id}", response_model=Status, responses={404: {"model": HTTPNotFoundError}})
async def get_newscard(news_id:int, token: str=Depends(oauth2_scheme)):
   return await NewsController.delete(news_id, token)


app.include_router(router)

if __name__ == '__main__':
    app = FastAPI()
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8000)