# models/exercise.py
"""Модели для упражнений КПТ"""
import random

class CBTExercise:
    """Базовый класс для упражнений КПТ"""

    def __init__(self, name, description, category, duration):
        self.name = name
        self.description = description
        self.category = category  # 'дыхание', 'мышление', 'релаксация', 'осознанность'
        self.duration = duration
        self.steps = []
        self.tips = []

    def add_step(self, step):
        self.steps.append(step)

    def add_tip(self, tip):
        self.tips.append(tip)

    def get_steps_count(self):
        return len(self.steps)

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'duration': self.duration,
            'steps': self.steps,
            'tips': self.tips
        }


class BreathingExercise(CBTExercise):
    """Упражнения на дыхание"""

    def __init__(self, name, description, duration):
        super().__init__(name, description, 'дыхание', duration)
        self.technique = None
        self.cycles = 5

    def set_technique(self, technique, inhale, hold, exhale):
        self.technique = {
            'name': technique,
            'inhale': inhale,
            'hold': hold,
            'exhale': exhale
        }


class CognitiveExercise(CBTExercise):
    """Когнитивные упражнения"""

    def __init__(self, name, description, duration):
        super().__init__(name, description, 'мышление', duration)
        self.prompts = []

    def add_prompt(self, prompt):
        self.prompts.append(prompt)


class RelaxationExercise(CBTExercise):
    """Упражнения на релаксацию"""

    def __init__(self, name, description, duration):
        super().__init__(name, description, 'релаксация', duration)


class ExerciseLibrary:
    """Библиотека всех упражнений КПТ"""

    def __init__(self):
        self.exercises = []
        self.categories = ['дыхание', 'мышление', 'релаксация', 'осознанность']
        self.init_exercises()

    def init_exercises(self):
        """Инициализация всех упражнений"""

        # 1. ДЫХАТЕЛЬНЫЕ УПРАЖНЕНИЯ
        ex1 = BreathingExercise(
            "🌬 Дыхание 4-7-8",
            "Техника для быстрого успокоения и снижения тревожности",
            5
        )
        ex1.set_technique("4-7-8", 4, 7, 8)
        ex1.add_step("Сядьте удобно, выпрямите спину")
        ex1.add_step("Положите кончик языка за верхние передние зубы")
        ex1.add_step("Выдохните полностью через рот со звуком")
        ex1.add_step("Закройте рот, вдохните через нос на 4 счета")
        ex1.add_step("Задержите дыхание на 7 счетов")
        ex1.add_step("Выдохните через рот на 8 счетов со звуком")
        ex1.add_step("Повторите цикл 4-5 раз")
        ex1.add_tip("Выполняйте упражнение 2 раза в день для лучшего эффекта")
        ex1.add_tip("Не перенапрягайтесь, со временем будет легче")
        self.exercises.append(ex1)

        ex2 = BreathingExercise(
            "🌊 Квадратное дыхание",
            "Техника для фокусировки и снятия стресса",
            5
        )
        ex2.set_technique("Квадрат", 4, 4, 4)
        ex2.add_step("Сядьте прямо, расслабьте плечи")
        ex2.add_step("Медленно вдохните через нос на 4 счета")
        ex2.add_step("Задержите дыхание на 4 счета")
        ex2.add_step("Медленно выдохните через рот на 4 счета")
        ex2.add_step("Задержите дыхание на 4 счета")
        ex2.add_step("Представляйте, как воздух движется по сторонам квадрата")
        ex2.add_step("Повторите 5-10 циклов")
        ex2.add_tip("Можно представлять, как рисуете квадрат в воздухе")
        self.exercises.append(ex2)

        ex3 = BreathingExercise(
            "🫁 Диафрагмальное дыхание",
            "Глубокое дыхание животом для полного расслабления",
            7
        )
        ex3.set_technique("Диафрагма", 5, 0, 5)
        ex3.add_step("Лягте на спину или сядьте удобно")
        ex3.add_step("Положите одну руку на грудь, другую на живот")
        ex3.add_step("Медленно вдохните через нос, направляя воздух в живот")
        ex3.add_step("Почувствуйте, как поднимается рука на животе")
        ex3.add_step("Медленно выдохните через рот, втягивая живот")
        ex3.add_step("Повторите 10 раз, концентрируясь на движении живота")
        ex3.add_tip("Грудь должна оставаться почти неподвижной")
        ex3.add_tip("Делайте выдох длиннее вдоха для большего расслабления")
        self.exercises.append(ex3)

        # 2. КОГНИТИВНЫЕ УПРАЖНЕНИЯ
        ex4 = CognitiveExercise(
            "🧠 Анализ автоматических мыслей",
            "Выявление и оспаривание негативных мыслей",
            15
        )
        ex4.add_step("Запишите ситуацию, которая вызвала дискомфорт")
        ex4.add_step("Определите автоматическую мысль, которая возникла")
        ex4.add_step("Оцените свою уверенность в этой мысли (0-100%)")
        ex4.add_step("Какие эмоции возникли? Оцените их интенсивность")
        ex4.add_step("Найдите доказательства ЗА эту мысль")
        ex4.add_step("Найдите доказательства ПРОТИВ этой мысли")
        ex4.add_step("Сформулируйте более сбалансированную мысль")
        ex4.add_step("Переоцените уверенность в исходной мысли")
        ex4.add_step("Оцените новые эмоции")
        ex4.add_prompt("Ситуация:")
        ex4.add_prompt("Автоматическая мысль:")
        ex4.add_prompt("Эмоции:")
        ex4.add_prompt("Доказательства ЗА:")
        ex4.add_prompt("Доказательства ПРОТИВ:")
        ex4.add_prompt("Альтернативная мысль:")
        ex4.add_tip("Ищите когнитивные искажения: катастрофизация, чтение мыслей, долженствование")
        ex4.add_tip("Спросите себя: 'Что бы я сказал другу в такой ситуации?'")
        self.exercises.append(ex4)

        ex5 = CognitiveExercise(
            "🎯 Техника заземления 5-4-3-2-1",
            "Быстрое возвращение в реальность при тревоге",
            5
        )
        ex5.add_step("Найдите 5 вещей, которые вы видите вокруг")
        ex5.add_step("Назовите их вслух или про себя")
        ex5.add_step("Найдите 4 вещи, которых вы можете коснуться")
        ex5.add_step("Почувствуйте их текстуру, температуру")
        ex5.add_step("Прислушайтесь к 3 звукам вокруг вас")
        ex5.add_step("Определите 2 запаха, которые чувствуете")
        ex5.add_step("Найдите 1 вкус, который ощущаете сейчас")
        ex5.add_step("Сделайте глубокий вдох")
        ex5.add_tip("Это упражнение особенно эффективно при панических атаках")
        ex5.add_tip("Можно выполнять с закрытыми глазами")
        self.exercises.append(ex5)

        ex6 = CognitiveExercise(
            "📝 Дневник благодарности",
            "Развитие позитивного мышления через благодарность",
            10
        )
        ex6.add_step("Запишите 3 вещи, за которые вы благодарны сегодня")
        ex6.add_step("Они могут быть очень простыми (вкусный чай, солнце, улыбка)")
        ex6.add_step("Для каждой вещи запишите, почему она важна")
        ex6.add_step("Почувствуйте благодарность в теле")
        ex6.add_step("Подумайте о человеке, которому вы благодарны")
        ex6.add_step("Если есть возможность, скажите им спасибо")
        ex6.add_tip("Ведите дневник ежедневно, это меняет мышление")
        ex6.add_tip("В трудные дни ищите даже маленькие поводы для благодарности")
        self.exercises.append(ex6)

        # 3. РЕЛАКСАЦИЯ
        ex7 = RelaxationExercise(
            "💆 Прогрессивная мышечная релаксация",
            "Постепенное напряжение и расслабление всех групп мышц",
            15
        )
        ex7.add_step("Сядьте или лягте удобно, закройте глаза")
        ex7.add_step("Сделайте несколько глубоких вдохов")
        ex7.add_step("Напрягите мышцы лица на 5 секунд... расслабьте")
        ex7.add_step("Поднимите плечи к ушам на 5 секунд... расслабьте")
        ex7.add_step("Сожмите кулаки на 5 секунд... расслабьте")
        ex7.add_step("Напрягите мышцы рук на 5 секунд... расслабьте")
        ex7.add_step("Напрягите мышцы спины на 5 секунд... расслабьте")
        ex7.add_step("Втяните живот на 5 секунд... расслабьте")
        ex7.add_step("Напрягите ягодицы на 5 секунд... расслабьте")
        ex7.add_step("Напрягите ноги на 5 секунд... расслабьте")
        ex7.add_step("Почувствуйте полное расслабление во всем теле")
        ex7.add_tip("Концентрируйтесь на разнице между напряжением и расслаблением")
        ex7.add_tip("Дышите глубоко во время упражнения")
        self.exercises.append(ex7)

        ex8 = RelaxationExercise(
            "🌈 Визуализация безопасного места",
            "Создание ментального убежища для отдыха",
            10
        )
        ex8.add_step("Сядьте удобно, закройте глаза")
        ex8.add_step("Сделайте несколько глубоких вдохов")
        ex8.add_step("Представьте место, где вы чувствуете себя в полной безопасности")
        ex8.add_step("Это может быть реальное или воображаемое место")
        ex8.add_step("Рассмотрите детали: цвета, формы, освещение")
        ex8.add_step("Какие звуки вы слышите в этом месте?")
        ex8.add_step("Какие запахи вы чувствуете?")
        ex8.add_step("Почувствуйте температуру воздуха")
        ex8.add_step("Прикоснитесь к предметам вокруг")
        ex8.add_step("Побудьте в этом месте несколько минут")
        ex8.add_step("Медленно вернитесь в реальность")
        ex8.add_tip("Это место всегда с вами, вы можете вернуться в любой момент")
        ex8.add_tip("С каждым разом визуализация будет становиться ярче")
        self.exercises.append(ex8)

        ex9 = RelaxationExercise(
            "☯️ Сканирование тела",
            "Осознанное внимание к каждой части тела",
            10
        )
        ex9.add_step("Лягте на спину, закройте глаза")
        ex9.add_step("Сделайте несколько глубоких вдохов")
        ex9.add_step("Направьте внимание на пальцы ног")
        ex9.add_step("Почувствуйте их, расслабьте")
        ex9.add_step("Медленно поднимайтесь вверх: стопы, голени, колени")
        ex9.add_step("Бедра, таз, живот, грудь")
        ex9.add_step("Пальцы рук, кисти, предплечья, плечи")
        ex9.add_step("Шея, лицо, голова")
        ex9.add_step("Почувствуйте расслабление во всем теле")
        ex9.add_step("Оставайтесь в этом состоянии несколько минут")
        ex9.add_tip("Не пытайтесь ничего изменить, просто наблюдайте")
        ex9.add_tip("Если отвлеклись, мягко верните внимание")
        self.exercises.append(ex9)

        # 4. ОСОЗНАННОСТЬ
        ex10 = CognitiveExercise(
            "🍵 Осознанное чаепитие",
            "Практика присутствия в моменте через обычное действие",
            7
        )
        ex10.add_step("Приготовьте чашку чая")
        ex10.add_step("Рассмотрите чашку: цвет, форму, текстуру")
        ex10.add_step("Почувствуйте тепло чашки в руках")
        ex10.add_step("Вдохните аромат чая, отметьте ноты")
        ex10.add_step("Сделайте маленький глоток")
        ex10.add_step("Почувствуйте вкус, температуру, текстуру")
        ex10.add_step("Проследите, как тепло распространяется по телу")
        ex10.add_step("Повторите, полностью присутствуя в моменте")
        ex10.add_tip("Можно делать с любой едой или напитком")
        ex10.add_tip("Замечайте, когда мысли уходят в прошлое или будущее")
        self.exercises.append(ex10)

        ex11 = CognitiveExercise(
            "🚶 Осознанная ходьба",
            "Медитация в движении",
            10
        )
        ex11.add_step("Встаньте, почувствуйте стопы на полу")
        ex11.add_step("Начните медленно идти")
        ex11.add_step("Почувствуйте, как стопа касается пола")
        ex11.add_step("Ощутите движение в ногах")
        ex11.add_step("Заметьте, как движутся руки")
        ex11.add_step("Почувствуйте дыхание во время ходьбы")
        ex11.add_step("Обратите внимание на окружающее: свет, цвета, звуки")
        ex11.add_step("Продолжайте 5-10 минут")
        ex11.add_tip("Можно ходить по комнате или на улице")
        ex11.add_tip("Не пытайтесь никуда успеть, просто идите")
        self.exercises.append(ex11)

    def get_exercises_by_category(self, category):
        """Получить упражнения по категории"""
        return [ex for ex in self.exercises if ex.category == category]

    def get_exercise_by_name(self, name):
        """Получить упражнение по названию"""
        for ex in self.exercises:
            if ex.name == name:
                return ex
        return None

    def get_random_exercise(self, category=None):
        """Получить случайное упражнение"""
        if category:
            exercises = self.get_exercises_by_category(category)
        else:
            exercises = self.exercises

        if exercises:
            return random.choice(exercises)
        return None