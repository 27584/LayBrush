from peewee import ForeignKeyField, Model, CharField, IntegerField, FloatField, DateTimeField, AutoField

from models.user import User
#######################################弃用


class UserDeck(Model):
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User)
    deck_index = IntegerField() # 1,2,3,4
    card_id = CharField()
    #card_index = IntegerField() # 1-10

    class Meta:
        table_name = 'user_decks'



