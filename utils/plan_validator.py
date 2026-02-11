"""
Валидация сгенерированных планов тренировок
Проверяет корректность плана по всем правилам:
- Структура данных
- Правила восстановления мышц
- Частота тренировок
- Доступность программ
- Распределение по частям
"""
from typing import List, Dict, Tuple, Any
from rules.recovery_rules import can_perform


class PlanValidator:
    """
    Валидатор для recommendedPlan.

    Проверяет:
    1. Структуру плана (поля, типы, диапазоны значений)
    2. Правила восстановления мышц
    3. Частоту тренировок по неделям
    4. Доступность программ в клубе
    5. Корректное распределение по частям (part 1 и 2)
    """

    def validate_plan(
        self,
        plan: List[Dict[str, Any]],
        recovery_rules: Dict[str, Dict],
        available_types: List[str],
        frequency: int,
        reshape_per_block: int = 0
    ) -> Tuple[bool, List[str]]:
        """
        Валидация плана на соответствие всем правилам.

        Args:
            plan: Список тренировок recommendedPlan
            recovery_rules: Правила восстановления мышц
            available_types: Доступные типы программ в клубе
            frequency: Целевая частота тренировок в неделю
            reshape_per_block: Лимит тренировок Reshape на этот блок (0 = недоступен)

        Returns:
            Tuple[bool, List[str]]: (is_valid, errors)
                - is_valid: True если план валиден
                - errors: Список ошибок (пустой если план валиден)
        """
        errors = []

        # 1. Проверка базовой структуры
        structure_errors = self._validate_structure(plan)
        errors.extend(structure_errors)

        # 2. Проверка количества тренировок
        count_errors = self._validate_workout_count(plan, frequency)
        errors.extend(count_errors)

        # 3. Проверка каждой тренировки
        for i, workout in enumerate(plan):
            workout_errors = self._validate_workout(workout, i + 1, available_types)
            errors.extend(workout_errors)

        # 4. Проверка правил восстановления
        recovery_errors = self._validate_recovery_rules(plan, recovery_rules)
        errors.extend(recovery_errors)

        # 5. Проверка частоты по неделям
        frequency_errors = self._validate_weekly_frequency(plan, frequency)
        errors.extend(frequency_errors)

        # 6. Проверка распределения по частям
        part_errors = self._validate_part_distribution(plan)
        errors.extend(part_errors)

        # 7. Проверка лимита Reshape на блок
        reshape_errors = self._validate_reshape_limit(plan, reshape_per_block)
        errors.extend(reshape_errors)

        is_valid = len(errors) == 0
        return is_valid, errors

    def _validate_structure(self, plan: List[Dict[str, Any]]) -> List[str]:
        """Проверка базовой структуры плана."""
        errors = []

        if not isinstance(plan, list):
            errors.append("План должен быть массивом (list)")
            return errors  # Критическая ошибка, дальше проверять нельзя

        if len(plan) == 0:
            errors.append("План пустой (0 тренировок)")
            return errors

        return errors

    def _validate_workout_count(self, plan: List[Dict], frequency: int) -> List[str]:
        """Проверка общего количества тренировок."""
        errors = []

        total_workouts = len(plan)
        min_workouts = frequency * 8  # 8 недель
        max_workouts = 5 * 8  # Максимум 5 тренировок в неделю × 8 недель

        if total_workouts < min_workouts or total_workouts > max_workouts:
            errors.append(
                f"Неверное общее количество тренировок: {total_workouts} "
                f"(ожидается {min_workouts}-{max_workouts} для частоты {frequency})"
            )

        return errors

    def _validate_workout(
        self,
        workout: Dict[str, Any],
        index: int,
        available_types: List[str]
    ) -> List[str]:
        """Проверка отдельной тренировки."""
        errors = []

        # Обязательные поля
        required_fields = ['text', 'week', 'day', 'programSetTypes', 'part']
        for field in required_fields:
            if field not in workout:
                errors.append(f"Тренировка {index}: отсутствует поле '{field}'")

        if 'week' in workout:
            week = workout['week']
            if not isinstance(week, int) or week < 1 or week > 8:
                errors.append(f"Тренировка {index}: неверная неделя {week} (должна быть 1-8)")

        if 'day' in workout:
            day = workout['day']
            if not isinstance(day, int) or day < 1 or day > 7:
                errors.append(f"Тренировка {index}: неверный день {day} (должен быть 1-7)")

        if 'part' in workout:
            part = workout['part']
            if not isinstance(part, int) or part < 1 or part > 2:
                errors.append(f"Тренировка {index}: неверная часть {part} (должна быть 1 или 2)")

        if 'programSetTypes' in workout:
            program_types = workout['programSetTypes']

            if not isinstance(program_types, list):
                errors.append(f"Тренировка {index}: programSetTypes должен быть массивом")
            elif len(program_types) == 0:
                errors.append(f"Тренировка {index}: programSetTypes пустой")
            else:
                # Проверка основного типа программы
                main_type = program_types[0]
                if main_type not in available_types:
                    errors.append(
                        f"Тренировка {index}: недоступный тип программы '{main_type}' "
                        f"(доступны: {', '.join(available_types)})"
                    )

                # Проверка альтернатив
                for alt_type in program_types[1:]:
                    if alt_type not in available_types:
                        errors.append(
                            f"Тренировка {index}: недоступная альтернатива '{alt_type}'"
                        )

        if 'text' in workout:
            text = workout['text']
            if not isinstance(text, str) or len(text) == 0:
                errors.append(f"Тренировка {index}: поле 'text' должно быть непустой строкой")

        return errors

    def _validate_recovery_rules(
        self,
        plan: List[Dict],
        recovery_rules: Dict[str, Dict]
    ) -> List[str]:
        """Проверка правил восстановления мышц."""
        errors = []

        # Группировка по неделям и проверка восстановления внутри недели
        for week in range(1, 9):
            week_workouts = [w for w in plan if w.get('week') == week]
            week_workouts.sort(key=lambda x: x.get('day', 0))

            for i, workout in enumerate(week_workouts):
                if 'programSetTypes' not in workout or not workout['programSetTypes']:
                    continue

                main_type = workout['programSetTypes'][0]

                # Получить предыдущие тренировки на этой неделе
                previous_workouts = week_workouts[:i]
                previous_types = [
                    w['programSetTypes'][0]
                    for w in previous_workouts
                    if 'programSetTypes' in w and w['programSetTypes']
                ]

                # Проверка возможности выполнения
                if not can_perform(main_type, previous_types):
                    day = workout.get('day', '?')
                    errors.append(
                        f"Неделя {week}, день {day}: нарушение восстановления для '{main_type}'. "
                        f"Слишком рано после предыдущих тренировок: {', '.join(previous_types[-3:])}"
                    )

        return errors

    def _validate_weekly_frequency(
        self,
        plan: List[Dict],
        target_frequency: int
    ) -> List[str]:
        """Проверка частоты тренировок по неделям."""
        errors = []

        for week in range(1, 9):
            week_workouts = [w for w in plan if w.get('week') == week]
            actual_frequency = len(week_workouts)

            if actual_frequency != target_frequency:
                errors.append(
                    f"Неделя {week}: неверная частота {actual_frequency} "
                    f"(ожидается {target_frequency})"
                )

        return errors

    def _validate_part_distribution(self, plan: List[Dict]) -> List[str]:
        """Проверка правильного распределения по частям (part 1 и 2)."""
        errors = []

        part1_workouts = [w for w in plan if w.get('part') == 1]
        part2_workouts = [w for w in plan if w.get('part') == 2]

        # Проверка что part 1 только в неделях 1-4
        part1_weeks = [w.get('week') for w in part1_workouts if 'week' in w]
        invalid_part1_weeks = [w for w in part1_weeks if w > 4]

        if invalid_part1_weeks:
            errors.append(
                f"Part 1 должен быть только в неделях 1-4, "
                f"но найден в неделях: {sorted(set(invalid_part1_weeks))}"
            )

        # Проверка что part 2 только в неделях 5-8
        part2_weeks = [w.get('week') for w in part2_workouts if 'week' in w]
        invalid_part2_weeks = [w for w in part2_weeks if w <= 4]

        if invalid_part2_weeks:
            errors.append(
                f"Part 2 должен быть только в неделях 5-8, "
                f"но найден в неделях: {sorted(set(invalid_part2_weeks))}"
            )

        # Проверка что нет тренировок без part
        workouts_without_part = [
            i + 1 for i, w in enumerate(plan)
            if 'part' not in w or w['part'] not in [1, 2]
        ]

        if workouts_without_part:
            errors.append(
                f"Тренировки без корректного part: {workouts_without_part[:5]}"
                + ("..." if len(workouts_without_part) > 5 else "")
            )

        return errors

    def _validate_reshape_limit(
        self,
        plan: List[Dict],
        reshape_per_block: int = 0
    ) -> List[str]:
        """
        Проверка лимита тренировок Reshape на блок.
        reshape_per_block рассчитан из pilatesVisits / кол-во блоков в абонементе.
        0 = reshape недоступен.
        """
        errors = []

        # Подсчёт reshape тренировок (основной тип = первый в programSetTypes)
        reshape_count = sum(
            1 for w in plan
            if w.get('programSetTypes') and w['programSetTypes'][0] == 'reshape'
        )

        if reshape_per_block <= 0 and reshape_count > 0:
            errors.append(
                f"В плане {reshape_count} тренировок Reshape, "
                f"но у атлета нет доступа к Reshape (нет pilatesVisits в абонементе)"
            )
        elif reshape_per_block > 0 and reshape_count > reshape_per_block:
            errors.append(
                f"Превышен лимит Reshape на блок: в плане {reshape_count}, "
                f"допустимо {reshape_per_block} (рассчитано из pilatesVisits абонемента)"
            )

        return errors

    def get_validation_summary(
        self,
        plan: List[Dict],
        recovery_rules: Dict[str, Dict],
        available_types: List[str],
        frequency: int
    ) -> Dict[str, Any]:
        """
        Получить детальную сводку валидации.

        Returns:
            Dict с информацией:
            - is_valid: bool
            - errors: List[str]
            - warnings: List[str]  (потенциальные проблемы, не критичные)
            - stats: Dict (статистика по плану)
        """
        is_valid, errors = self.validate_plan(plan, recovery_rules, available_types, frequency)

        # Статистика
        stats = {
            'total_workouts': len(plan),
            'weeks': len(set(w.get('week') for w in plan if 'week' in w)),
            'part1_workouts': len([w for w in plan if w.get('part') == 1]),
            'part2_workouts': len([w for w in plan if w.get('part') == 2]),
            'program_type_distribution': self._get_type_distribution(plan)
        }

        # Предупреждения (не ошибки, но стоит обратить внимание)
        warnings = []

        # Проверка баланса типов программ
        distribution = stats['program_type_distribution']
        total = sum(distribution.values())

        # Слишком много одного типа
        for ptype, count in distribution.items():
            percentage = (count / total) * 100 if total > 0 else 0
            if percentage > 50:
                warnings.append(
                    f"Тип программы '{ptype}' составляет {percentage:.1f}% плана "
                    f"(возможно слишком много)"
                )

        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'stats': stats
        }

    def _get_type_distribution(self, plan: List[Dict]) -> Dict[str, int]:
        """Подсчёт распределения типов программ."""
        distribution = {}

        for workout in plan:
            if 'programSetTypes' in workout and workout['programSetTypes']:
                main_type = workout['programSetTypes'][0]
                distribution[main_type] = distribution.get(main_type, 0) + 1

        return distribution
