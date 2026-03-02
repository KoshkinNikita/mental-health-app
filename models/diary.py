# models/diary.py
"""Модели для записей дневника"""

import json
from datetime import datetime


class DiaryEntry:
    """Запись в дневнике мыслей"""

    def __init__(self, entry_id=None, user_id=None, situation="",
                 emotions=None, thoughts="", distortions=None,
                 alternative_thought=None, reassessment=None,
                 created_at=None):
        self.id = entry_id
        self.user_id = user_id
        self.situation = situation
        self.emotions = emotions or {}
        self.thoughts = thoughts
        self.distortions = distortions or []
        self.alternative_thought = alternative_thought
        self.reassessment = reassessment
        self.created_at = created_at or datetime.now()

    @classmethod
    def from_db_row(cls, row):
        """Создать запись из строки БД"""
        if not row:
            return None

        return cls(
            entry_id=row['id'],
            user_id=row['user_id'],
            situation=row['situation'],
            emotions=json.loads(row['emotions']),
            thoughts=row['thoughts'],
            distortions=json.loads(row['distortions']),
            alternative_thought=row['alternative_thought'],
            reassessment=row['reassessment'],
            created_at=datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
        )

    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'situation': self.situation,
            'emotions': self.emotions,
            'thoughts': self.thoughts,
            'distortions': self.distortions,
            'alternative_thought': self.alternative_thought,
            'reassessment': self.reassessment,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }