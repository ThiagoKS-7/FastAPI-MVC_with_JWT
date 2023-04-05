import jwt
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from passlib.hash import bcrypt
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from dotenv import dotenv_values
from models import User, NewsCard


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


async def check_superuser(token: str=Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    try:
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password" )
    
    if user.is_superuser:
        return await User_Pydantic.from_tortoise_orm(user)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permission" )


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
    user_obj = User(username=user.username, email=user.email, password_hash=bcrypt.hash(user.password_hash), is_superuser=False)
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)

@router.post("/admin/new", response_model=User_Pydantic)
async def create_user_admin(user: UserIn_Pydantic, token: str=Depends(oauth2_scheme)):
    if token:
        user_obj = User(username=user.username, email=user.email, password_hash=bcrypt.hash(user.password_hash), is_superuser=user.is_superuser)
        await user_obj.save()
        return await User_Pydantic.from_tortoise_orm(user_obj)
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permission" )
    
@router.get("/users/me", response_model=User_Pydantic)
async def get_user(user: UserIn_Pydantic=Depends(get_current_user)):
    return user



@router.post("/news/add", response_model=News_Pydantic)
async def create_newscard( data: NewsIn_Pydantic, token: str=Depends(oauth2_scheme)):
    if token:
        news_obj = NewsCard(name=data.name, description=data.description)
        await news_obj.save()
        return await News_Pydantic.from_tortoise_orm(news_obj)
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permission" )

@router.get("/news", response_model=News_Pydantic)
async def list_newscards():
    return await News_Pydantic.from_queryset(NewsCard.all())

@router.get("/news/{news_id}", response_model=News_Pydantic, responses={404: {"model": HTTPNotFoundError}})
async def get_newscard(news_id:int):
    return await News_Pydantic.from_queryset_single(NewsCard.get(id=news_id))

@router.put("/news/{news_id}", response_model=News_Pydantic, responses={404: {"model": HTTPNotFoundError}})
async def get_newscard(news_id:int, news: NewsIn_Pydantic):
    await NewsCard.filter(id=news_id).update(**news.dict(exclude_unset=True))
    return await News_Pydantic.from_queryset_single(NewsCard.get(id=news_id))
    
@router.get("/news/{news_id}", response_model=News_Pydantic, responses={404: {"model": HTTPNotFoundError}})
async def get_newscard(news_id:int):
    deleted_count = await NewsCard.filter(id=news_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"News {news_id} not found")
    return {
            "status": status.HTTP_200_OK,
            "message":f"Deleted news {news_id}"
        }

app.include_router(router)