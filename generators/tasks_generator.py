"""
Генерация tasksProgress из recommendedPlan
Подсчитывает количество каждого типа программы и создаёт задачи для отслеживания
"""
from typing import List, Dict, Any
from collections import Counter


class TasksGenerator:
    """
    Генерирует tasksProgress на основе recommendedPlan.

    Логика:
    - Подсчитывает количество каждого типа программы в плане
    - Группирует похожие типы (push/pull, legs/gluteLab) для гибкости
    - Создаёт задачи отдельно для part 1 (недели 1-4) и part 2 (недели 5-8)
    - Группирует задачи по неделям появления
    """

    # Группы похожих программ (можно выполнить любую из группы)
    PROGRAM_GROUPS = {
        'push_pull': {
            'types': ['push', 'pull'],
            'display_name': 'Push или Pull',
            'description': 'Тренировка верха тела'
        },
        'legs_glute': {
            'types': ['legs', 'gluteLab'],
            'display_name': 'Legs или GluteLab',
            'description': 'Тренировка ног и ягодиц'
        },
        # Можно добавить другие группы если нужно
    }

    # Маппинг типов программ к названиям для задач
    PROGRAM_TYPE_NAMES = {
        'bootcamp': 'BootCamp',
        'metcon': 'MetCon',
        'legs': 'Legs',
        'gluteLab': 'Glute',
        'upperBody': 'Upper Body',
        'fullBody': 'Full Body',
        'functionalFullBody': 'Functional Full Body',
        'push': 'Push',
        'pull': 'Pull',
        'armBlast': 'Arms',
        'reshape': 'Reshape',
        'mindAndBody': 'Mind & Body',
        'assessment': 'Assessment',
        'education': 'Education',
        'endGame': 'End Game'
    }

    def generate(self, recommended_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Генерировать tasksProgress из recommendedPlan.

        Args:
            recommended_plan: Список тренировок

        Returns:
            Список задач tasksProgress
        """
        if not recommended_plan:
            return []

        # Разделить план на части
        part1_plan = [w for w in recommended_plan if w.get('part') == 1]
        part2_plan = [w for w in recommended_plan if w.get('part') == 2]

        # Генерировать задачи для каждой части
        tasks = []
        tasks.extend(self._generate_tasks_for_part(part1_plan, part=1))
        tasks.extend(self._generate_tasks_for_part(part2_plan, part=2))

        return tasks

    def _generate_tasks_for_part(
        self,
        workouts: List[Dict[str, Any]],
        part: int
    ) -> List[Dict[str, Any]]:
        """
        Генерировать задачи для одной части (part 1 или 2).

        Args:
            workouts: Список тренировок для этой части
            part: Номер части (1 или 2)

        Returns:
            Список задач для этой части
        """
        if not workouts:
            return []

        # Подсчёт количества каждого типа программы
        type_counts = Counter()
        type_first_week = {}  # Первая неделя появления каждого типа
        available_alternatives = set()  # Все типы доступные в альтернативах

        for workout in workouts:
            if 'programSetTypes' not in workout or not workout['programSetTypes']:
                continue

            main_type = workout['programSetTypes'][0]
            type_counts[main_type] += 1

            # Запомнить первую неделю
            week = workout.get('week', 1)
            if main_type not in type_first_week or week < type_first_week[main_type]:
                type_first_week[main_type] = week

            # Собрать все альтернативы
            for alt_type in workout['programSetTypes'][1:]:
                available_alternatives.add(alt_type)

        # Группировать похожие типы (учитывая альтернативы)
        grouped_tasks = self._group_similar_types(type_counts, type_first_week, available_alternatives)

        # Создать задачи
        tasks = []

        for group_info in grouped_tasks:
            task = self._create_task(
                program_types=group_info['types'],
                display_name=group_info['display_name'],
                target=group_info['target'],
                part=part,
                week=group_info['week']
            )
            tasks.append(task)

        # Сортировать задачи по неделе появления
        tasks.sort(key=lambda t: (t['part'], t['week']))

        return tasks

    def _group_similar_types(
        self,
        type_counts: Counter,
        type_first_week: Dict[str, int],
        available_alternatives: set
    ) -> List[Dict[str, Any]]:
        """
        Группировать похожие типы программ (push/pull, legs/gluteLab).
        Учитывает типы в альтернативах - если legs в плане, а gluteLab в альтернативах,
        создаёт задачу "Legs или GluteLab" для гибкости.

        Args:
            type_counts: Количество каждого типа
            type_first_week: Первая неделя появления каждого типа
            available_alternatives: Типы доступные в альтернативах

        Returns:
            Список групп для создания задач
        """
        grouped = []
        processed_types = set()

        # Проверяем каждую группу
        for group_name, group_config in self.PROGRAM_GROUPS.items():
            group_types = group_config['types']

            # Находим типы из этой группы которые есть в плане ИЛИ в альтернативах
            present_in_plan = [t for t in group_types if t in type_counts and t not in processed_types]
            available_in_alts = [t for t in group_types if t in available_alternatives and t not in present_in_plan]

            # Если хотя бы один тип в плане и другие доступны в альтернативах
            if len(present_in_plan) >= 1 and (len(present_in_plan) > 1 or len(available_in_alts) > 0):
                # Объединяем типы из плана и альтернатив для гибкости
                all_group_types = present_in_plan + available_in_alts

                # Подсчёт только для типов которые есть в плане
                total_count = sum(type_counts[t] for t in present_in_plan)
                first_week = min(type_first_week.get(t, 1) for t in present_in_plan)

                grouped.append({
                    'types': all_group_types,
                    'display_name': group_config['display_name'],
                    'target': total_count,
                    'week': first_week
                })

                # Отмечаем только типы из плана как обработанные
                processed_types.update(present_in_plan)

            elif len(present_in_plan) == 1 and len(available_in_alts) == 0:
                # Если только один тип из группы и нет альтернатив, создаём обычную задачу
                ptype = present_in_plan[0]
                grouped.append({
                    'types': [ptype],
                    'display_name': self.PROGRAM_TYPE_NAMES.get(ptype, ptype.title()),
                    'target': type_counts[ptype],
                    'week': type_first_week.get(ptype, 1)
                })
                processed_types.add(ptype)

        # Добавляем оставшиеся типы (не входящие в группы)
        for ptype, count in type_counts.items():
            if ptype not in processed_types:
                grouped.append({
                    'types': [ptype],
                    'display_name': self.PROGRAM_TYPE_NAMES.get(ptype, ptype.title()),
                    'target': count,
                    'week': type_first_week.get(ptype, 1)
                })

        return grouped

    def _create_task(
        self,
        program_types: List[str],
        display_name: str,
        target: int,
        part: int,
        week: int
    ) -> Dict[str, Any]:
        """
        Создать одну задачу для типа(ов) программы.

        Args:
            program_types: Список типов программ (может быть группа)
            display_name: Название для отображения
            target: Целевое количество
            part: Номер части (1 или 2)
            week: Первая неделя появления

        Returns:
            Задача в формате tasksProgress
        """
        # Форматировать текст задачи
        if target == 1:
            text = f"Выполни 1 тренировку {display_name}"
        elif 2 <= target <= 4:
            text = f"Выполни {target} тренировки {display_name}"
        else:
            text = f"Выполни {target} тренировок {display_name}"

        return {
            'text': text,
            'programSetTypes': program_types,  # Массив типов (гибкость!)
            'part': part,
            'target': target,
            'done': 0,
            'week': week
        }

    def get_tasks_summary(self, tasks_progress: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Получить сводку по задачам.

        Args:
            tasks_progress: Список задач

        Returns:
            Сводка с статистикой
        """
        summary = {
            'total_tasks': len(tasks_progress),
            'part1_tasks': len([t for t in tasks_progress if t.get('part') == 1]),
            'part2_tasks': len([t for t in tasks_progress if t.get('part') == 2]),
            'total_target_workouts': sum(t.get('target', 0) for t in tasks_progress),
            'tasks_by_type': {}
        }

        # Группировка по типам
        for task in tasks_progress:
            program_types = task.get('programSetTypes', [])
            if program_types:
                ptype = program_types[0]
                if ptype not in summary['tasks_by_type']:
                    summary['tasks_by_type'][ptype] = {
                        'count': 0,
                        'target': 0,
                        'parts': []
                    }

                summary['tasks_by_type'][ptype]['count'] += 1
                summary['tasks_by_type'][ptype]['target'] += task.get('target', 0)
                summary['tasks_by_type'][ptype]['parts'].append(task.get('part'))

        return summary

    def validate_tasks_against_plan(
        self,
        tasks_progress: List[Dict[str, Any]],
        recommended_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проверить соответствие tasksProgress и recommendedPlan.

        Args:
            tasks_progress: Сгенерированные задачи
            recommended_plan: Исходный план

        Returns:
            Результат проверки с ошибками (если есть)
        """
        errors = []

        # Подсчёт программ в плане
        plan_counts = Counter()
        for workout in recommended_plan:
            if 'programSetTypes' in workout and workout['programSetTypes']:
                main_type = workout['programSetTypes'][0]
                plan_counts[main_type] += 1

        # Подсчёт задач
        task_counts = Counter()
        for task in tasks_progress:
            program_types = task.get('programSetTypes', [])
            if program_types:
                ptype = program_types[0]
                task_counts[ptype] += task.get('target', 0)

        # Проверка соответствия
        all_types = set(plan_counts.keys()) | set(task_counts.keys())

        for ptype in all_types:
            plan_count = plan_counts.get(ptype, 0)
            task_count = task_counts.get(ptype, 0)

            if plan_count != task_count:
                errors.append(
                    f"Несоответствие для типа '{ptype}': "
                    f"в плане {plan_count}, в задачах {task_count}"
                )

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'plan_counts': dict(plan_counts),
            'task_counts': dict(task_counts)
        }
