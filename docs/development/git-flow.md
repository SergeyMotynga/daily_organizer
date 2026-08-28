# Git Flow и Commit Flow

## Ветки

- `main` - стабильная production-ветка.
- `develop` - рабочая интеграционная ветка.
- feature-ветки создаются от `develop`.
- feature-ветки вливаются только в `develop`.
- `main` получает изменения только из `develop`.
- напрямую работать в `main` нельзя.
- напрямую работать в `develop` нельзя.

## Именование веток

```text
feature/<short-name>
fix/<short-name>
chore/<short-name>
docs/<short-name>
refactor/<short-name>
test/<short-name>
```

Примеры:

```text
feature/v0.1-foundation
feature/v0.1-auth
feature/v0.1-task-crud
feature/v0.1-today-view
feature/v0.1-frontend-shell
fix/refresh-cookie
docs/api-contract
test/task-filters
```

## Коммиты

Используем Conventional Commits.

```text
feat: add task creation endpoint
fix: handle expired refresh sessions
chore: configure ruff and pytest
docs: update v0.1 api contract
test: cover today view grouping
refactor: split task service logic
```

Основные типы:

- `feat` - новая функциональность.
- `fix` - исправление бага.
- `chore` - технические изменения без бизнес-поведения.
- `docs` - документация.
- `test` - тесты.
- `refactor` - изменение структуры без изменения поведения.
- `style` - форматирование.
- `ci` - CI/CD и проверки.

## Правила PR

- один PR должен закрывать одну понятную задачу или небольшой связанный набор изменений.
- изменения backend-логики требуют тестов.
- API/auth/task rules требуют тестов.
- форматирование, линтер и тесты должны проходить перед merge в `develop`.
- незавершенные эксперименты не попадают в `main`.

## Правило для Codex

Codex не должен писать код прямо в `main` или `develop`.

Перед изменениями Codex должен проверить текущую ветку. Если это `main` или `develop`, сначала нужно создать или переключиться на отдельную ветку от `develop`.
