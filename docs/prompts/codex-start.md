# Стартовый промпт для Codex

Используй этот промпт в начале новой задачи Codex по этому репозиторию.

```text
Ты работаешь в репозитории Daily Organizer.

Контекст проекта:
- Это pet-проект личного органайзера.
- v0.1 функционально готова и является daily-first to-do list.
- Долгосрочно приложение должно развиваться в органайзер с задачами, заметками, проектами, планами, отчетами, финансами и будущей MCP-интеграцией.
- Поэтому нельзя проектировать общий app shell как todo-only приложение.

Перед началом работы прочитай локально:
1. README.md
2. docs/project.md
3. docs/development/git-flow.md
4. docs/development/codex-working-rules.md
5. docs/version/v0.1/README.md
6. docs/version/v0.2/plan.md

Источник истины по продукту находится в Notion и Miro:
- Notion проект: https://app.notion.com/p/3c7678c73f47819599c6eb5a53b79a08
- ТЗ v0.1: https://app.notion.com/p/3c9678c73f47816295cbe25045da7def
- Фичлист v0.1: https://app.notion.com/p/3c9678c73f4781a092ebfe80640c5bce
- Черновой контракт MCP: https://app.notion.com/p/3c9678c73f478108a62ec3ea269aae7b
- Miro v0.1: https://miro.com/app/board/uXjVHtjh-Lk=/?moveToWidgets=AQAP2sfJgPKEgIAwAQEBevitDgEC8eYND4OYQQEB28cDx6vBGA

Не дублируй продуктовые решения в repo docs. Если задача требует уточнить scope, API, БД, UI или MCP - используй Notion/Miro как источник истины.

Git flow:
- main - production-stable.
- develop - интеграционная ветка.
- Работать можно только в feature/fix/chore/docs/test/refactor ветке от develop.
- Если текущая ветка main или develop, сначала создай отдельную ветку под задачу.
- Коммиты в стиле Conventional Commits.

Текущая версия:
- v0.1: auth, tasks, Today view, Planning, Calendar, Archive, task drawers, deadline time, recurring tasks, date filters, adaptive UI.
- Не входят: notes, finance, AI/MCP implementation, reminders, mobile app, VPS deploy.

Стек:
- Backend: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic, uv.
- Frontend: React, TypeScript, Vite, React Router, TanStack Query, @daypicker/react, react-aria-components, custom CSS.
- Dev infra: Docker Compose, Taskfile или Makefile, ruff, mypy/pyright, pytest, pre-commit, .editorconfig.

Архитектура backend:
- API layer -> service layer -> repository/ORM layer.
- Бизнес-логика должна жить в service layer.
- Repository/ORM отвечает за CRUD и запросы.
- API layer отвечает за маршруты, DTO и HTTP-контракт.

Правила разработки:
- Не придумывай новые продуктовые решения молча, если они не описаны в документации.
- Если решение не зафиксировано, сначала предложи варианты и спроси.
- Если задача четкая, реализуй ее полностью и проверь.
- Не дублируй бизнес-логику.
- Не добавляй абстракции заранее ради красоты.
- Идентификаторы в коде на английском.
- Комментарии и docstring можно писать на русском.
- Для backend-логики добавляй тесты.
- Не меняй чужие несвязанные изменения.

После выполнения:
- Кратко опиши, что изменено.
- Укажи, какие проверки запускались.
- Если проверки не запускались, объясни почему.
- Для ревью сначала перечисли найденные проблемы с файлами/строками.
```
