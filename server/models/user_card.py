from peewee import ForeignKeyField, Model, CharField, IntegerField, FloatField, DateTimeField, AutoField

from models.user import User
#######################################弃用

class UserCard(Model):
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User)
    card_id = CharField()
    level = IntegerField(default=0) #0表示未拥有
    number = IntegerField(default=0)

    class Meta:
        table_name = 'user_cards'

    @classmethod
    def get_card_level(cls,uid,card_id):
        card = cls.get_or_none(
            cls.user_id == uid,
            cls.card_id == card_id
        )
        return card.level if card else 0





