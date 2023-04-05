from tortoise import fields
from passlib.hash import bcrypt
from tortoise.models import Model 

class User(Model):
    id = fields.IntField(pk=True)
    username= fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)
    
    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)