# Daily Organizer

Daily Organizer - pet-проект личного органайзера.

Долгосрочная идея: собрать в одном приложении задачи, заметки, планы, отчеты, финансы и будущую интеграцию с AI через MCP.

Первая версия специально маленькая: `v0.1` - это daily-first to-do list с авторизацией, задачами, экраном "Сегодня", планированием, календарем, архивом, PostgreSQL, FastAPI, React и тестами.

## Документация

- [Обзор проекта](docs/project.md)
- [Daily Organizer v0.1](docs/version/v0.1/README.md)
- [Черновой план v0.2](docs/version/v0.2/plan.md)
- [Git flow](docs/development/git-flow.md)
- [Стартовый промпт для Codex](docs/prompts/codex-start.md)

Подробные продуктовые документы не дублируются в репозитории. Источник истины:

- [Notion: проект](https://app.notion.com/p/3c7678c73f47819599c6eb5a53b79a08)
- [Notion: ТЗ v0.1](https://app.notion.com/p/3c9678c73f47816295cbe25045da7def)
- [Notion: Фичлист v0.1](https://app.notion.com/p/3c9678c73f4781a092ebfe80640c5bce)
- [Notion: Черновой контракт MCP](https://app.notion.com/p/3c9678c73f478108a62ec3ea269aae7b)
- [Miro: v0.1 схемы и UI](https://miro.com/app/board/uXjVHtjh-Lk=/?moveToWidgets=AQAP2sfJgPKEgIAwAQEBevitDgEC8eYND4OYQQEB28cDx6vBGA)

## Текущий статус

Текущая стабильная точка: `v0.1` функционально готова.

`v0.2` начинается с app structure refactor: task module выделяется под `/app/tasks/*`, после чего добавляется модуль личных проектов с Kanban- и list-представлениями.

Модель веток:

- `main` - стабильная production-ветка.
- `develop` - интеграционная рабочая ветка.
- разработка идет только в feature/fix/chore/docs/test/refactor ветках от `develop`.

Подробности: [Git flow](docs/development/git-flow.md).

## Локальный запуск

Backend:

```powershell
task docker:up
task backend:run
```

Frontend:

```powershell
cd frontend
npm install
cd ..
task frontend:dev
```

Frontend dev server запускается на `http://localhost:5173` и проксирует `/api` в локальный backend.
