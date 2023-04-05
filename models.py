from tortoise import fields
from passlib.hash import bcrypt
from tortoise.models import Model 

class User(Model):
    id = fields.IntField(pk=True)
    username= fields.CharField(50, unique=True)
    email= fields.CharField(255, unique=True)
    password_hash = fields.CharField(128)
    is_superuser = fields.BooleanField(default=False)
    
    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)
    
    
class NewsCard(Model):
    id = fields.IntField(pk=True)
    name= fields.CharField(128, unique=True)
    description= fields.TextField()
    
    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)