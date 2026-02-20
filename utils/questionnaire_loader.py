"""
Загрузка анкеты из CSV файла для тестирования
На этапе разработки используем CSV, потом переключимся на userblocks.forms
"""
import csv
import os
from typing import Dict, Optional, Any


class QuestionnaireLoader:
    """Загружает анкету из CSV файла."""

    # Маппинг значений из CSV в формат системы
    GENDER_MAP = {
        'Мужской': 'male',
        'Женский': 'female'
    }

    FORM_MAP = {
        'Худощавое (мало веса и мышц)': 'худощавое',
        'Среднее (обычное телосложение)': 'среднее',
        'Плотное/Крепкое (есть мышцы, но и лишний вес)': 'плотное',
        'Спортивное (тело в тонусе, тренируюсь регулярно)': 'спортивное',
        'Полное (большой избыточный вес)': 'полное'
    }

    GOAL_MAP = {
        'Похудение': 'похудение',
        'Набор мышечной массы': 'масса',
        'Тонус и рельеф': 'рельеф',
        'Улучшение здоровья и выносливости': 'здоровье',
        'Поддержание текущей формы': 'поддержание'
    }

    FOCUS_MAP = {
        'Верх тела': 'верх_тела',
        'Ноги и ягодицы': 'ноги',
        'Выносливость': 'выносливость',
        'Баланс и мобильность': 'баланс'
    }

    # Маппинг по ключевым словам — устойчив к изменениям текста в Google Forms
    EXPERIENCE_KEYWORDS = {
        'профи': ['профи', 'опытный', 'продвинутый', 'advanced', 'pro', 'системно'],
        'любитель': ['любитель', 'регулярно', 'средний', 'intermediate', 'уверенный'],
        'новичок': ['новичок', 'начинающий', 'beginner', 'нерегулярно', 'редко'],
    }

    BREAK_MAP = {
        'Перерыва нет, тренируюсь сейчас': 0,
        'До 2 недель': 7,
        '2-4 недели': 21,
        '1-3 месяца': 60,
        'Более 3 месяцев': 120
    }

    @staticmethod
    def load_from_csv(csv_path: str, phone_or_name: str) -> Optional[Dict[str, Any]]:
        """
        Загрузить анкету из CSV файла.

        Args:
            csv_path: Путь к CSV файлу
            phone_or_name: Номер телефона или имя для поиска

        Returns:
            Dict с данными анкеты или None
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Поиск по имени или телефону
                    name = row.get('Ваше имя ', '').strip()
                    phone = row.get('Укажите ваш номер телефона', '').strip()

                    if phone_or_name in name or phone_or_name in phone:
                        return QuestionnaireLoader._parse_row(row)

            return None

        except Exception as e:
            import logging
            logging.error(f"Ошибка при загрузке анкеты из CSV: {e}")
            return None

    @staticmethod
    def _parse_row(row: Dict[str, str]) -> Dict[str, Any]:
        """Преобразовать строку CSV в формат questionnaire."""

        # Парсинг фокусных областей
        focus_raw = row.get('Дополнительный фокус (можно выбрать несколько) ', '')
        focus_areas = []
        for focus_csv, focus_sys in QuestionnaireLoader.FOCUS_MAP.items():
            if focus_csv in focus_raw:
                focus_areas.append(focus_sys)

        # Ограничения по здоровью - передаём как есть (raw text)
        # LLM сам разберётся что написал человек
        health_raw = row.get('Есть ли у вас ограничения по здоровью?', '').strip()

        # Если написано "нет", пусто, или вариации "всё ок" - оставляем пустым
        health_lower = health_raw.lower()
        no_restriction_phrases = ['нет', 'no', '', 'нету', 'не имею',
                                  'под контролем', 'под собственным контролем',
                                  'все в порядке', 'всё в порядке', 'без ограничений']
        if any(phrase in health_lower for phrase in no_restriction_phrases):
            health_restrictions = ''
        else:
            health_restrictions = health_raw  # Raw text напрямую

        # Получение значений из маппингов
        gender = QuestionnaireLoader.GENDER_MAP.get(row.get('Пол', ''), 'male')
        current_form = QuestionnaireLoader._get_mapped_value(
            row.get('Как бы вы описали свою текущую форму?', ''),
            QuestionnaireLoader.FORM_MAP,
            'среднее'
        )
        goal = QuestionnaireLoader._get_mapped_value(
            row.get('Основная фитнес-цель', ''),
            QuestionnaireLoader.GOAL_MAP,
            'здоровье'
        )
        experience = QuestionnaireLoader._match_experience(
            row.get('Ваш реальный стаж тренировок ', '')
        )
        current_break = QuestionnaireLoader._get_mapped_value(
            row.get('Текущий перерыв в тренировках', ''),
            QuestionnaireLoader.BREAK_MAP,
            0
        )

        # Формирование questionnaire
        questionnaire = {
            'name': row.get('Ваше имя ', '').strip(),
            'phone': row.get('Укажите ваш номер телефона', '').strip(),
            'gender': gender,
            'age': int(row.get('Возраст', 25)),
            'height': int(row.get('Рост (см)', 170)),
            'weight': int(row.get('Вес (кг)', 70)),
            'current_form': current_form,
            'goal': goal,
            'focus': focus_areas,
            'experience': experience,
            'current_break': current_break,
            'health_restrictions': health_restrictions
        }

        return questionnaire

    @staticmethod
    def _match_experience(csv_value: str) -> str:
        """Определить уровень опыта по ключевым словам (устойчиво к изменениям Google Forms)."""
        text = csv_value.lower().strip()
        if not text:
            return 'новичок'

        # Проверяем от высшего к низшему — если есть "профи", это профи даже если есть и другие слова
        for level in ['профи', 'любитель', 'новичок']:
            for keyword in QuestionnaireLoader.EXPERIENCE_KEYWORDS[level]:
                if keyword in text:
                    return level

        return 'новичок'

    @staticmethod
    def _get_mapped_value(csv_value: str, mapping: Dict, default):
        """Получить значение из маппинга с fallback на default."""
        csv_value = csv_value.strip()

        # Точное совпадение
        if csv_value in mapping:
            return mapping[csv_value]

        # Частичное совпадение
        for key, value in mapping.items():
            if key in csv_value or csv_value in key:
                return value

        return default


def load_questionnaire_for_user(user_id: str = None, phone_or_name: str = None) -> Optional[Dict[str, Any]]:
    """
    Загрузить анкету для пользователя.

    Args:
        user_id: MongoDB ObjectId пользователя (не используется для CSV)
        phone_or_name: Номер телефона или имя для поиска в CSV

    Returns:
        Dict с анкетой или None
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data',
        'Анкета для составления программы тренировок  (Responses) - Form Responses 1.csv'
    )

    if phone_or_name:
        return QuestionnaireLoader.load_from_csv(csv_path, phone_or_name)

    return None
