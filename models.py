from peewee import (Model, FloatField, PostgresqlDatabase,
                    IntegerField, BooleanField)

db = PostgresqlDatabase(database='bot_db', user='postgres',
                        password='mysecretpassword', host='localhost',
                        port='5432')


class BaseModel(Model):
    """Модель подключения к БД."""

    class Meta:
        database = db


class User(BaseModel):
    """Модель пользователя."""
    user_id = IntegerField(primary_key=True)
    subscribed = BooleanField(default=False)


class UserRate(BaseModel):
    """Модель запросов пользователя."""
    user_id = IntegerField()
    rate = FloatField(default=0)
