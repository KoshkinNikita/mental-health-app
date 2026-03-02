# models/user.py
"""Модель пользователя"""


class User:
    """Класс пользователя"""

    def __init__(self, user_id=None, username=None, name=None):
        self.id = user_id
        self.username = username
        self.name = name

    @classmethod
    def from_db_row(cls, row):
        """Создать пользователя из строки БД"""
        if not row:
            return None
        return cls(
            user_id=row['id'],
            username=row['username'],
            name=row['name']
        )

    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name
        }