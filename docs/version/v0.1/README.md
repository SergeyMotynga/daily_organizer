# Daily Organizer v0.1

`v0.1` - первая рабочая версия Daily Organizer.

Цель версии: сделать daily-first to-do list, которым можно пользоваться вручную без AI, MCP и внешних интеграций.

## Статус

`v0.1` считается функционально готовой.

Версия не означает production-релиз. Это внутренняя стабильная точка проекта: базовая продуктовая логика собрана, UI пересобран по макетам, основные сценарии проверены вручную и автотестами.

## Что вошло

- Регистрация, вход, refresh/logout и текущая сессия.
- App shell с адаптивной навигацией.
- Экран `Сегодня`.
- Экран `Планирование`.
- Экран `Календарь` с неделей и месяцем.
- Экран `Архив`.
- Создание, редактирование, просмотр и удаление задач.
- Статусы задач: `todo` и `done`.
- Архивация через `archived_at`, независимо от статуса выполнения.
- Плановая дата и время задачи.
- Дедлайн с датой и временем.
- Today-блоки, включая входящие, план на сегодня, дедлайны, просрочку и выполненные задачи.
- Фильтры планирования: быстрые фильтры, конкретная дата, диапазон дат, статусы, поиск и сортировка.
- Повторяющиеся задачи:
  - `daily`;
  - `weekdays`;
  - `weekly`;
  - интервалы вроде "каждые 3 дня" или "каждые 2 недели";
  - completion history по конкретной дате через `task_recurrence_completions`.
- Календарный view API для диапазона.
- Date picker на `@daypicker/react`.
- Адаптивный frontend для desktop/mobile.
- Frontend UI rebuild по v0.1-макетам.

## Текущая модель задач

- `status_code` отвечает только за выполнение: `todo` или `done`.
- Архив определяется через `archived_at`.
- Обычная выполненная задача получает `completed_at`.
- Повторяющаяся задача остается правилом в `tasks`.
- Выполнение повторяющейся задачи на конкретную дату хранится в `task_recurrence_completions`.
- Перевод повторяющейся задачи обратно в `none` очищает completion history.
- Удаление задачи каскадно удаляет completion history.

## Ключевые API

- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `PATCH /api/v1/tasks/{task_id}`
- `DELETE /api/v1/tasks/{task_id}`
- `GET /api/v1/task-statuses`
- `GET /api/v1/task-recurrence-types`
- `GET /api/v1/task-views/today`
- `GET /api/v1/calendar`
- `PUT /api/v1/tasks/{task_id}/recurrence-completions/{occurrence_date}`
- `DELETE /api/v1/tasks/{task_id}/recurrence-completions/{occurrence_date}`

## Что сознательно не вошло

- Production deploy, домен, VPS, HTTPS и CI/CD.
- Напоминания и уведомления.
- Исключения/переносы отдельных occurrences повторяющихся задач.
- Streaks и статистика привычек.
- Заметки.
- Проекты и группировка задач.
- Финансы.
- AI/MCP-интеграция.
- Нативное мобильное приложение.

## Проверки

Перед закрытием v0.1 использовались:

```powershell
npm run check
npm run build
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

Если `task.exe` в среде недоступен из-за WinGet-ссылки, запускаются эквивалентные команды напрямую.
