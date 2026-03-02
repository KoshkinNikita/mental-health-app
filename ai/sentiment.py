# ai/sentiment.py
"""Анализатор тональности и эмоций текста"""


class SentimentAnalyzer:
    """Анализатор тональности и эмоций текста"""

    def __init__(self):
        # Словари эмоциональной лексики
        self.positive_words = {
            'хорошо', 'отлично', 'прекрасно', 'замечательно', 'радостно', 'счастлив',
            'круто', 'супер', 'классно', 'великолепно', 'восхитительно', 'превосходно',
            'спокойно', 'уютно', 'комфортно', 'приятно', 'доволен', 'рад', 'счастье',
            'улыбка', 'смех', 'позитив', 'энергия', 'бодрость', 'вдохновение'
        }

        self.negative_words = {
            'плохо', 'ужасно', 'грустно', 'тоскливо', 'одиноко', 'страшно', 'тревожно',
            'больно', 'тяжело', 'невыносимо', 'отчаяние', 'безнадежно', 'беспомощно',
            'злость', 'гнев', 'раздражение', 'обида', 'вина', 'стыд', 'кошмар',
            'депрессия', 'апатия', 'усталость', 'бессилие', 'пустота', 'тоска'
        }

        self.anxiety_words = {
            'тревога', 'страх', 'боюсь', 'паника', 'паническая', 'беспокойство',
            'переживаю', 'волнуюсь', 'напряжение', 'стресс', 'нервы', 'нервничаю',
            'кошмар', 'ужас', 'опасность', 'угроза', 'катастрофа', 'беда'
        }

        self.anger_words = {
            'злость', 'гнев', 'ярость', 'бешенство', 'раздражение', 'ненависть',
            'презираю', 'отвращение', 'возмущение', 'негодование', 'обида', 'злюсь'
        }

        self.sadness_words = {
            'грусть', 'печаль', 'тоска', 'уныние', 'скорбь', 'горе', 'плакать',
            'слезы', 'одиночество', 'безысходность', 'отчаяние', 'депрессия'
        }

        self.joy_words = {
            'радость', 'счастье', 'восторг', 'ликование', 'блаженство', 'эйфория',
            'удовольствие', 'наслаждение', 'веселье', 'смех', 'улыбка'
        }

        # Эмодзи и их эмоциональная окраска
        self.emoji_map = {
            '😊': 'positive', '😄': 'positive', '😁': 'positive', '😂': 'positive',
            '🥰': 'positive', '😍': 'positive', '🤗': 'positive', '😌': 'positive',
            '😔': 'negative', '😢': 'negative', '😭': 'negative', '😞': 'negative',
            '😟': 'negative', '😰': 'negative', '😨': 'negative', '😱': 'negative',
            '😠': 'anger', '😡': 'anger', '🤬': 'anger',
            '😐': 'neutral', '😶': 'neutral', '🤔': 'neutral'
        }

    def analyze_sentiment(self, text):
        """
        Анализ тональности текста
        Возвращает: {'sentiment': 'positive/negative/neutral/mixed',
                     'score': float от -1 до 1,
                     'emotions': {'joy': 0.0, 'sadness': 0.0, 'anger': 0.0, 'anxiety': 0.0},
                     'intensity': float 0-1}
        """
        text_lower = text.lower()

        # Подсчет слов по категориям
        word_count = len(text_lower.split())
        if word_count == 0:
            return {'sentiment': 'neutral', 'score': 0.0, 'emotions': {}, 'intensity': 0.0}

        # Счетчики эмоций
        emotions = {
            'joy': 0,
            'sadness': 0,
            'anger': 0,
            'anxiety': 0
        }

        # Общий счет тональности
        positive_score = 0
        negative_score = 0

        # Анализ слов
        words = text_lower.split()
        for word in words:
            word = word.strip('.,!?;:"\'()[]{}')

            if word in self.positive_words:
                positive_score += 1
                if word in self.joy_words:
                    emotions['joy'] += 1
            elif word in self.negative_words:
                negative_score += 1
                if word in self.sadness_words:
                    emotions['sadness'] += 1
                elif word in self.anger_words:
                    emotions['anger'] += 1
                elif word in self.anxiety_words:
                    emotions['anxiety'] += 1

        # Анализ эмодзи
        for char in text:
            if char in self.emoji_map:
                emoji_type = self.emoji_map[char]
                if emoji_type == 'positive':
                    positive_score += 2
                    emotions['joy'] += 1
                elif emoji_type == 'negative':
                    negative_score += 2
                    emotions['sadness'] += 1
                elif emoji_type == 'anger':
                    negative_score += 3
                    emotions['anger'] += 1

        # Расчет общего балла
        total = positive_score + negative_score
        if total > 0:
            sentiment_score = (positive_score - negative_score) / total
        else:
            sentiment_score = 0.0

        # Определение тональности
        if sentiment_score > 0.3:
            sentiment = 'positive'
        elif sentiment_score < -0.3:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # Нормализация эмоций
        max_emotion = max(emotions.values()) if emotions.values() else 1
        normalized_emotions = {
            emotion: count / max_emotion if max_emotion > 0 else 0.0
            for emotion, count in emotions.items()
        }

        # Интенсивность
        intensity = min(1.0, (positive_score + negative_score) / (word_count + 1) * 2)

        return {
            'sentiment': sentiment,
            'score': round(sentiment_score, 2),
            'emotions': normalized_emotions,
            'intensity': round(intensity, 2)
        }

    def get_dominant_emotion(self, sentiment_data):
        """Получить доминирующую эмоцию"""
        emotions = sentiment_data['emotions']
        if not emotions:
            return None

        dominant = max(emotions.items(), key=lambda x: x[1])
        if dominant[1] > 0.3:
            return dominant[0]
        return None