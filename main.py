import jwt
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from dotenv import dotenv_values
from models import User

config = dotenv_values(".env") 
env = dict(config.items())
JWT_SECRET = env["JWT_SECRET"]


router = APIRouter(prefix="/api/v1")
app = FastAPI()

@app.get('/')
async def index():
    return RedirectResponse("/docs", status_code=301)

register_tortoise(
    app,
    db_url=env["MYSQL_URL"],
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

async def authenticate_user(username: str, password: str,):
    user = await User.get(username=username)
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user

async def get_current_user(token: str=Depends(oauth2_scheme)):
    print(token, JWT_SECRET)
    payload = jwt.decode(token, JWT_SECRET, algorithm="HS256")
    try:
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password" )
    
    return await User_Pydantic.from_tortoise_orm(user)

@app.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials" )
    
    
    user_obj = await User_Pydantic.from_tortoise_orm(user)
    token = jwt.encode({"id": user_obj.id, "username": user_obj.username}, JWT_SECRET)
    print(token)
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

@router.get('/docs')
async def index():
    return RedirectResponse("/docs", status_code=301)

@router.post("/users", response_model=User_Pydantic)
async def create_user(user: UserIn_Pydantic=Depends(get_current_user)):
    user_obj = User(username=user.username, password_hash=bcrypt.hash(user.password_hash))
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)
    
@router.get("/users/me", response_model=User_Pydantic)
async def get_user(user: UserIn_Pydantic=Depends(get_current_user)):
    return user

app.include_router(router)