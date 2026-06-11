from typing import List

from peewee import ForeignKeyField, Model, CharField, IntegerField, FloatField, DateTimeField, AutoField


"""
用户表
"""

class User(Model):
    id = AutoField(primary_key=True)
    phcathub_uid = IntegerField()
    name = CharField(max_length=100, default="无名之人")
    image = CharField(max_length=100, default="")
    coin = IntegerField(default=0)
    deck_index = IntegerField(default=1)

    class Meta:
        table_name = 'users'

    @classmethod
    def new_user(cls, phcathub_uid):
        from models.user_card import UserCard
        from models.user_deck import UserDeck
        name = random_name_generator()
        user = User.create(phcathub_uid=phcathub_uid,name = name)
        for card in ["mouse","test1","test2","test3"]:
            UserCard.create(user = user,card_id = card,level=1)
            for deck_index in range(1,5):
                UserDeck.create(user = user,card_id = card,deck_index = deck_index)
        return user

    def get_deck_by_index(self, index):
        from models.user_deck import UserDeck
        cards = UserDeck.select().where(UserDeck.user == self).where(UserDeck.deck_index == index)
        deck = []
        for card in cards:
            deck.append(card.card_id)
        return deck

import random

def random_name_generator():
    adjectives = [
        "快乐的", "暴躁的", "呆萌的", "嚣张的", "佛系的",
        "叛逆的", "油腻的", "清爽的", "疯狂的", "温柔的",
        "沙雕的", "高冷的", "话痨的", "社恐的", "社牛的"
    ]
    nouns = [
        "勾八", "二哈", "憨憨", "冤种", "显眼包",
        "老六", "卷王", "摆烂哥", "摸鱼怪", "干饭魂",
        "躺平侠", "显眼仔", "打工仔", "熬夜党", "秃头佬"
    ]

    adj = random.choice(adjectives)
    noun = random.choice(nouns)
    num = random.randint(00, 99)
    name = f"{adj}{noun}{num:02d}"


    return name


