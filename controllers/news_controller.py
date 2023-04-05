from fastapi import HTTPException,status
from models import NewsCard
from tortoise.contrib.pydantic import pydantic_model_creator

News_Pydantic = pydantic_model_creator(NewsCard, name="News")
NewsIn_Pydantic = pydantic_model_creator(NewsCard, name="NewsIn", exclude_readonly=True)

class NewsController():
    def __init__(self):
        pass
    async def create(data, token):
        if token:
            news_obj = NewsCard(name=data.name, description=data.description)
            await news_obj.save()
            return await News_Pydantic.from_tortoise_orm(news_obj)
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permission" )
    
    async def get_all():
        try:
            res = await News_Pydantic.from_queryset(NewsCard.all())
            return [{"id": i.id, "name": i.name, "description": i.description} for i in res]
        except Exception as e:
            return  HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e) 
    
    async def get_one(news_id:int):
        try:
            return await News_Pydantic.from_queryset_single(NewsCard.get(id=news_id))
        except Exception as e:
            return  HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e) 
        
    async def update(news_id:int, news, token:str):
        try:
            if token:
                await NewsCard.filter(id=news_id).update(**news.dict(exclude_unset=True))
                return await News_Pydantic.from_queryset_single(NewsCard.get(id=news_id))
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permission" )
        except Exception as e:
            return  HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e) 
    
    async def delete(news_id:int, token: str):
        if token:
            deleted_count = await NewsCard.filter(id=news_id).delete()
            if not deleted_count:
                raise HTTPException(status_code=404, detail=f"News {news_id} not found")
            return {
                    "status": status.HTTP_200_OK,
                    "message":f"Deleted news {news_id}"
                }
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permission" )