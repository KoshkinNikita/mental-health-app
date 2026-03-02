# ai/mental_health_bot.py
"""Интеллектуальный чат-бот для поддержки ментального здоровья"""

import random
from datetime import datetime


class MentalHealthBot:
    """Интеллектуальный чат-бот для поддержки ментального здоровья"""

    def __init__(self, db, user_id=None):
        self.db = db
        self.user_id = user_id
        self.context = {
            'last_topic': None,
            'user_mood': None,
            'conversation_history': [],
            'suggested_exercises': [],
            'emergency_mode': False
        }

        # Приветствия
        self.greetings = [
            "Привет! Как ты сегодня? 🌼",
            "Здравствуй! Рада тебя видеть. Как настроение? 🌸",
            "Приветствую! Чем могу помочь сегодня? 💫",
            "Здравствуй! Как проходит твой день? 🌿"
        ]

        # Словарь ответов по темам
        self.responses = {
            'тревога': [
                "Я слышу, что ты испытываешь тревогу. Это нормальная реакция. Давай попробуем дыхательное упражнение? 🌬️",
                "Тревога может быть очень тяжелой. Помни, что это временное состояние. Хочешь сделать упражнение на заземление? 🌱",
                "Когда тревога накрывает, попробуй технику 5-4-3-2-1. Назови 5 вещей, которые видишь, 4, которые чувствуешь, 3 звука, 2 запаха и 1 вкус."
            ],
            'грусть': [
                "Грустить — это нормально. Ты не один. Что обычно помогает тебе почувствовать себя лучше? 💙",
                "Мне жаль, что тебе грустно. Хочешь поговорить о том, что случилось? Иногда просто выговориться помогает.",
                "Грусть — как волна, она приходит и уходит. Помни, что за дождем всегда выходит солнце. ☀️"
            ],
            'гнев': [
                "Злость — это сигнал, что что-то не так. Попробуй сделать глубокий вдох и медленный выдох. 🔥",
                "Когда чувствуешь гнев, важно не подавлять его, но и не выплескивать разрушительно. Может, побить подушку? 💢",
                "Гнев часто маскирует другие чувства — боль, страх, обиду. Что стоит за твоим гневом?"
            ],
            'усталость': [
                "Усталость — сигнал, что нужен отдых. Разреши себе pause. 🌙",
                "Ты много делаешь! Помни, что отдых так же важен, как работа. Хочешь технику быстрого расслабления?",
                "Даже 5 минут тишины могут восстановить силы. Попробуй закрыть глаза и просто посидеть в тишине."
            ],
            'одиночество': [
                "Чувство одиночества знакомо многим. Помни, что ты не один, даже если сейчас так кажется. 🤗",
                "Даже среди людей можно чувствовать себя одиноким. Что обычно приносит тебе чувство связи с другими?",
                "Одиночество — это не про количество людей вокруг, а про качество связей. Ты важен и ценен сам по себе."
            ]
        }

        # Мотивирующие цитаты
        self.quotes = [
            "«Ты сильнее, чем думаешь, и смелее, чем кажется»",
            "«Маленькие шаги каждый день ведут к большим переменам»",
            "«Забота о себе — не эгоизм, а необходимость»",
            "«Сегодня ты сделал все, что мог, и этого достаточно»",
            "«Ты не обязан быть идеальным, чтобы быть ценным»",
            "«Лучший способ предсказать будущее — создать его»",
            "«Будь добр к себе — ты делаешь все, что в твоих силах»",
            "«Ты заслуживаешь покоя и счастья прямо сейчас»"
        ]

        # Упражнения КПТ
        self.exercises = {
            'дыхание': {
                'name': '🌬️ Дыхание 4-7-8',
                'instructions': [
                    "Сядь удобно, выпрями спину",
                    "Вдохни через нос на 4 счета",
                    "Задержи дыхание на 7 счетов",
                    "Медленно выдохни через рот на 8 счетов",
                    "Повтори 4 раза"
                ]
            },
            'заземление': {
                'name': '🌱 Техника 5-4-3-2-1',
                'instructions': [
                    "Назови 5 вещей, которые видишь вокруг",
                    "Назови 4 вещи, которые чувствуешь (текстуры, температура)",
                    "Назови 3 звука, которые слышишь",
                    "Назови 2 запаха, которые чувствуешь",
                    "Назови 1 вкус, который ощущаешь"
                ]
            },
            'мысли': {
                'name': '🧠 Анализ автоматических мыслей',
                'instructions': [
                    "Запиши ситуацию, которая вызвала дискомфорт",
                    "Запиши автоматическую мысль, которая пришла",
                    "Найди доказательства ЗА эту мысль",
                    "Найди доказательства ПРОТИВ этой мысли",
                    "Сформулируй более сбалансированную мысль"
                ]
            },
            'благодарность': {
                'name': '💝 Дневник благодарности',
                'instructions': [
                    "Запиши 3 вещи, за которые ты благодарен сегодня",
                    "Они могут быть очень простыми (вкусный чай, солнце, улыбка прохожего)",
                    "Почувствуй благодарность в теле"
                ]
            }
        }

    def get_response(self, message):
        """Получить ответ бота на сообщение пользователя"""
        message = message.lower().strip()

        self.context['conversation_history'].append({
            'user': message,
            'timestamp': datetime.now()
        })

        if self.is_emergency(message):
            self.context['emergency_mode'] = True
            return self.get_emergency_response()

        if any(word in message for word in ['упражнение', 'упражнения', 'помоги', 'помощь', 'сделать']):
            return self.suggest_exercise(message)

        if any(word in message for word in ['привет', 'здравствуй', 'хай', 'здарова']):
            return random.choice(self.greetings)

        for emotion, responses in self.responses.items():
            if emotion in message:
                self.context['last_topic'] = emotion
                return random.choice(responses)

        if any(word in message for word in ['цитата', 'мотивация', 'вдохновение']):
            return self.get_random_quote()

        if any(word in message for word in ['как дела', 'как ты', 'что нового']):
            return self.get_mood_check_response()

        return self.get_general_response(message)

    def is_emergency(self, message):
        """Проверка на экстренную ситуацию"""
        emergency_words = [
            'плохо', 'умираю', 'убью', 'ненавижу', 'не хочу жить',
            'самоубийство', 'больно', 'крик', 'тошно', 'терпеть нет сил',
            'плохая мысль', 'страшно', 'кошмар'
        ]
        return any(word in message for word in emergency_words)

    def get_emergency_response(self):
        """Ответ в экстренной ситуации"""
        return """🚨 **Если тебе прямо сейчас очень плохо:**

1. **Позвони на горячую линию**: 8-800-2000-122 (круглосуточно, бесплатно)
2. **Напиши в чат помощи**: https://psyhelp.ru/chat
3. **Сделай заземление**: Назови 5 вещей, которые видишь вокруг
4. **Дыши глубоко**: Вдох на 4, задержка на 4, выдох на 6

Ты не один. Пожалуйста, обратись за помощью. 💝

Хочешь, я предложу упражнение, которое поможет прямо сейчас?"""

    def suggest_exercise(self, message):
        """Предложить упражнение"""
        if 'дыхание' in message:
            exercise = self.exercises['дыхание']
        elif 'заземление' in message or '5-4-3-2-1' in message:
            exercise = self.exercises['заземление']
        elif 'мысл' in message:
            exercise = self.exercises['мысли']
        elif 'благодарность' in message:
            exercise = self.exercises['благодарность']
        else:
            exercise = random.choice(list(self.exercises.values()))

        response = f"**{exercise['name']}**\n\n"
        for i, step in enumerate(exercise['instructions'], 1):
            response += f"{i}. {step}\n"

        self.context['suggested_exercises'].append(exercise['name'])

        return response

    def get_random_quote(self):
        """Получить случайную цитату"""
        return f"💭 {random.choice(self.quotes)}"

    def get_mood_check_response(self):
        """Ответ на вопрос о состоянии"""
        if self.user_id and self.db:
            today_mood = self.db.get_today_mood(self.user_id)

            if today_mood:
                mood_icons = {1: '😔', 2: '😕', 3: '😐', 4: '🙂', 5: '😊',
                              6: '😄', 7: '😁', 8: '😎', 9: '🤗', 10: '🥳'}
                icon = mood_icons.get(today_mood, '😐')
                return f"Сегодня твое настроение: {icon} {today_mood}/10\n\nА как у меня? Я здесь, чтобы поддерживать тебя! 🌟"

        return "У меня все отлично! Я здесь, чтобы помогать тебе. Расскажи, как ты? 🌼"

    def get_general_response(self, message):
        """Общий ответ на непонятное сообщение"""
        general_responses = [
            f"Расскажи подробнее, я слушаю 👂",
            f"Как ты к этому относишься?",
            f"Я здесь, чтобы поддержать тебя. Что ты чувствуешь сейчас?",
            f"Хочешь поговорить об этом или сделать упражнение?",
            f"Это важно. Расскажи, что еще ты чувствуешь?",
            f"Спасибо, что делишься. Как я могу помочь тебе сейчас?"
        ]
        return random.choice(general_responses)

    def analyze_sentiment(self, message):
        """Простой анализ тональности сообщения"""
        positive_words = ['хорошо', 'радостно', 'счастье', 'круто', 'отлично', 'прекрасно']
        negative_words = ['плохо', 'грустно', 'тоскливо', 'ужасно', 'больно', 'страшно']

        message_lower = message.lower()

        pos_count = sum(1 for word in positive_words if word in message_lower)
        neg_count = sum(1 for word in negative_words if word in message_lower)

        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'

    def get_personalized_recommendation(self):
        """Получить персонализированную рекомендацию на основе истории"""
        if not self.user_id or not self.db:
            return None

        mood_entries = self.db.get_mood_entries(self.user_id, days=7)

        if len(mood_entries) >= 3:
            avg_mood = sum(e['mood_score'] for e in mood_entries) / len(mood_entries)

            if avg_mood < 4:
                return "📉 Я вижу, что настроение в последнее время ниже среднего. Хочешь попробовать упражнение на поднятие настроения?"
            elif avg_mood > 7:
                return "📈 Отличная динамика! Рад, что у тебя хорошее настроение. Продолжай в том же духе!"

        return None