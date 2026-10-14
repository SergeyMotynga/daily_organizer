# Граф Daily Organizer

Снимок от 14 октября 2026 года, исходный коммит `b7b8c0c5b316e7f33fab4e2afade7cde1a4eb5f2`. Версия graphifyy: `0.9.89`.

## Состав корпуса

- Обработано 195 файлов: 167 файлов кода, 12 документов и 16 макетов.
- В коде 46,819 слов, в документации 3,768; PNG анализировались визуально.
- Предупреждение детектора: большой корпус, около 712,182 слов. Эта оценка завышена: детектор считает бинарные PNG как текст.
- Ещё 20 файлов не классифицированы: среди них CSS, TOML-инструкции агентов, Dockerfile и lock-файл backend. Их содержание не извлечено.
- `.env`, виртуальные окружения, node_modules, build-каталоги и служебные данные Git исключены.
- Внешние страницы Notion и Miro представлены ссылками из документов; их содержимое не читалось.

## Результат

- 1976 узлов, 4850 связей, 114 групп.
- EXTRACTED — явная связь в источнике; INFERRED — вывод агента; AMBIGUOUS — неопределённая связь.
- Связи по достоверности: EXTRACTED: 4431, INFERRED: 419.
- Расход токенов: AST — 0 LLM-токенов; точный расход семантического помощника недоступен в инструменте. Нули служебного cost.json — заглушки, а не измерение бесплатного анализа.
- Граф неориентированный: для направлений вызовов проверяйте source_location и исходный код.

## Проверка целостности

- Связи с неизвестными узлами: 268.
- Связи без концов: 0.
- Петли: 2.
- Связи между одинаковыми парами, объединённые при сборке: 241.
- Предупреждение: простой граф объединяет связи между одной парой узлов; часть типов отношений теряется. Граф пригоден для навигации, но не представляет каждую исходную связь отдельно.

## Центральные узлы

- `User` — 87 связей.
- `auth_client()` — 87 связей.
- `TaskService` — 77 связей.

## Связи между группами

- `Слои API → service → repository/ORM` → `Слои API → service → repository/ORM`: `semantically_similar_to`, INFERRED.
  Источники: `AGENTS.md` → `docs/development/codex-working-rules.md`.
- `Правила агентов Daily Organizer` → `Gitflow и доставка изменений`: `references`, EXTRACTED.
  Источники: `AGENTS.md` → `docs/development/git-flow.md`.
- `Daily Organizer: README` → `Gitflow и доставка изменений`: `references`, EXTRACTED.
  Источники: `README.md` → `docs/development/git-flow.md`.

## Вопросы для исследования

- Как модель `User` связывает авторизацию, задачи и проекты?
- Какие выведенные связи `User`, `get_current_user()`, `change_password()` подтверждаются исходниками?
- Как связаны с остальной системой `backend`, `@types/node`, `@types/react`?

## Группы и связность

| Группа | Узлов | Связность (cohesion) | Центральные символы |
|---|---:|---:|---|
| Бизнес-логика задач | 91 | 0.044444444444444446 | TaskService, Task, .update_task(), exceptions/tasks.py |
| Контракт и типы задач | 80 | 0.056329113924050635 | services/tasks.py, v1/tasks.py, TaskStatusCode, TaskRecurrenceTypeCode |
| Пользователи и ORM-модели | 80 | 0.046202531645569624 | User, services/auth.py, task.py, user.py |
| Зависимости и task views | 66 | 0.047086247086247084 | deps.py, typing, get_task_service(), v1/task_views.py |
| Клиентские API и запросы | 60 | 0.0807909604519774 | projects/queries.ts, apiRequest(), tasks/queries.ts, task/types.ts |
| Общие интеграционные тесты | 56 | 0.06883116883116883 | pytest, httpx, sqlalchemy, tasks/helpers.py |
| Маршрутизация и сессия frontend | 55 | 0.08350168350168351 | routes.tsx, react, session.ts, AppRoutes() |
| Авторизация и доменные ошибки | 54 | 0.06568832983927324 | AuthService, exceptions/auth.py, errors/auth.py, AuthError |
| Формы и детали задач | 48 | 0.10017730496453901 | task-details-drawer.tsx, TaskDetailsDrawer(), task-form-fields.tsx, create-task-drawer.tsx |
| Запросы хранилища задач | 47 | 0.058279370952821465 | TaskRepository, UUID, .list_tasks_for_user(), date |
| Планирование и архив | 47 | 0.08695652173913043 | planning-page.tsx, PlanningPage(), archive-page.tsx, ArchivePage() |
| Refresh и смена пароля | 45 | 0.07575757575757576 | register_user(), login_user(), auth/helpers.py, test_password.py |
| Тесты сервиса проектов | 45 | 0.12222222222222222 | test_project_service.py, make_project(), make_service(), make_user() |
| Тесты фильтрации задач | 43 | 0.10741971207087486 | auth_client(), test_list.py, anyio, AsyncClient |
| Календарь и выбор дат | 43 | 0.09634551495016612 | calendar-page.tsx, CalendarPage(), date-picker-popover.tsx, DatePickerPopover() |
| Бизнес-логика проектов | 41 | 0.08536585365853659 | ProjectService, services/projects.py, Project, dto/projects.py |
| Экраны и настройки проектов | 41 | 0.1 | project-page.tsx, lucide-react, project-settings-drawer.tsx, SelectCombobox() |
| Колонки и перенос задач | 40 | 0.09871794871794871 | ProjectColumn, ProjectCompletionColumnRequiredError, .move_task(), .bulk_move_tasks() |
| Время и приоритеты задач | 38 | 0.07823613086770982 | utc_now(), security.py, test_deadline_presets.py, test_done_today_uses_completed_at_date() |
| Зависимости и сборка frontend | 37 | 0.05555555555555555 | package.json, dependencies, devDependencies, scripts |
| Запуск и обработка ошибок | 36 | 0.08412698412698413 | handlers.py, main.py, register_exception_handlers(), validation_error_handler() |
| Тесты изменения задач | 35 | 0.11596638655462185 | create_task(), test_update.py, anyio, AsyncClient |
| Доступ и endpoints проектов | 33 | 0.125 | get_current_user(), get_project_service(), update_project(), create_project_column() |
| HTTP-схемы проектов | 31 | 0.10752688172043011 | v1/projects.py, schemas/projects.py, BaseModel, ProjectResponse |
| Запросы хранилища проектов | 31 | 0.08602150537634409 | ProjectRepository, UUID, .get_project_for_user(), .clear_completion_column() |
| Тесты проектных сценариев | 31 | 0.17204301075268819 | test_project_workflows.py, auth_client(), create_project(), AsyncClient |
| Экран Сегодня | 29 | 0.12315270935960591 | today-page.tsx, isTaskRecurring(), TodayPage(), Checkbox() |
| Тесты создания задач | 28 | 0.12962962962962962 | test_create.py, anyio, AsyncClient, test_create_task_validates_recurrence() |
| HTTP endpoints задач | 27 | 0.10256410256410256 | list_tasks(), move_task(), update_task(), complete_task_recurrence() |
| Ошибки проектных правил | 26 | 0.13230769230769232 | exceptions/projects.py, RecurringTaskCompletionColumnError, errors/projects.py, InvalidTaskProjectError |
| Провайдеры и общий frontend | 25 | 0.12333333333333334 | index.ts, app.tsx, providers.tsx, @tanstack/react-query |
| HTTP endpoints авторизации | 23 | 0.1422924901185771 | get_auth_service(), refresh(), login(), logout() |
| Тесты API проектов | 23 | 0.1976284584980237 | test_projects.py, auth_client(), create_project(), AsyncClient |
| Конфигурация TypeScript приложения | 19 | 0.10526315789473684 | compilerOptions, tsconfig.app.json, allowJs, allowSyntheticDefaultImports |
| Токены и тесты security | 16 | 0.175 | get_settings(), decode_access_token(), test_security.py, test_decode_access_token_returns_user_id_for_valid_token() |
| Тесты часовых поясов | 16 | 0.16666666666666666 | test_today_timezone.py, test_done_today_uses_user_local_day(), _local_datetime_utc(), test_today_view_rejects_invalid_timezone() |
| Тесты dev-сброса пароля | 15 | 0.20952380952380953 | test_dev_reset_password.py, test_dev_reset_password_updates_password_and_revokes_sessions(), anyio, AsyncClient |
| Cookies авторизации | 14 | 0.2087912087912088 | v1/auth.py, cookies.py, set_access_cookie(), set_auth_cookies() |
| Фильтры и mapping запросов | 14 | 0.14285714285714285 | list_projects(), query_params.py, normalize_optional_query_text(), _project_response() |
| Конфигурация TypeScript tooling | 14 | 0.14285714285714285 | compilerOptions, tsconfig.node.json, allowJs, isolatedModules |
| HTTP-схемы авторизации | 13 | 0.19230769230769232 | schemas/auth.py, ChangePasswordRequest, DevResetPasswordRequest, LoginRequest |
| Тесты входа | 13 | 0.23076923076923078 | test_login.py, test_login_rejects_invalid_payload(), test_login_rejects_wrong_password(), test_login_sets_auth_cookies() |
| Фикстуры и очистка БД | 13 | 0.23076923076923078 | test_sessionmaker(), client(), clean_data_tables(), fixture |
| Продуктовая идея и roadmap | 13 | 0.15384615384615385 | Daily Organizer: README, Обзор проекта Daily Organizer, Сначала стабильное ручное приложение, затем AI/MCP, Ручной daily-first сценарий без AI/MCP |
| Тестовое окружение БД | 12 | 0.19696969696969696 | integration/conftest.py, get_test_database_url(), test_engine(), get_test_migration_database_url() |
| Настройки и сессии БД | 12 | 0.21212121212121213 | config.py, session.py, get_db(), get_sessionmaker() |
| План и модули v0.2 | 12 | 0.21212121212121213 | Daily Organizer v0.2: черновой план, Task module под /app/tasks/* и отдельная группа навигации, Канонические маршруты /app/tasks/* с legacy redirects, Общий app shell для новых модулей |
| Документация и инженерные правила | 11 | 0.18181818181818182 | Правила работы с Codex, Индекс локальной документации, Слои API → service → repository/ORM, Слои API → service → repository/ORM |
| Миграции auth и recurrence | 11 | 0.18181818181818182 | 202608300001_create_auth_tables.py, 202609100001_add_task_deadline_time_and_recurrence.py, sqlalchemy_dialects, upgrade() |
| Миграции планирования и архива | 11 | 0.18181818181818182 | collections_abc, 202609090001_add_task_planned_time.py, upgrade(), 202609090002_decouple_task_archiving.py |
| Тесты регистрации | 11 | 0.23636363636363636 | test_register_rejects_invalid_payload(), anyio, AsyncClient, test_register_creates_user() |
| Правила backend-слоёв | 10 | 0.26666666666666666 | Правила агентов Daily Organizer, Service: бизнес-логика и транзакции, API: HTTP mapping и зависимости, Schemas: HTTP Pydantic schemas |
| Конфигурация backend | 10 | 0.2 | Settings, .__init__(), .cors_origin_list(), .is_dev_mode() |
| Тесты текущего пользователя | 10 | 0.26666666666666666 | test_me_rejects_access_token_for_unknown_user(), test_me_returns_current_user(), anyio, AsyncClient |
| Тесты справочников повторений | 10 | 0.24444444444444444 | test_create_task_rejects_inactive_recurrence_type(), test_list_task_recurrence_types_returns_active_reference(), test_list_task_recurrence_types_requires_auth(), anyio |
| Модель задач v0.1 | 10 | 0.26666666666666666 | Daily Organizer v0.1: завершённая функциональная версия, task_recurrence_completions: выполнение на дату, Recurrence none очищает history; удаление каскадное, PUT/DELETE recurrence-completions/{occurrence_date} |
| Окружение миграций Alembic | 9 | 0.2777777777777778 | env.py, get_migration_database_url(), run_migrations_offline(), run_migrations_online() |
| Тесты календарного API | 9 | 0.25 | test_calendar_returns_range_items_and_recurrence_completions(), test_calendar_rejects_invalid_range(), calendar_titles(), anyio |
| Тесты выполнения повторений | 9 | 0.3333333333333333 | test_daily_recurrence_completion_is_scoped_to_occurrence_date(), test_weekdays_recurrence_is_hidden_on_weekend(), test_weekly_interval_and_archive_control_today_visibility(), anyio |
| Тесты удаления задач | 8 | 0.35714285714285715 | test_delete_recurring_task_cascades_completion_history(), test_delete_task_removes_row_physically(), anyio, async_sessionmaker |
| Тесты владения задачами | 8 | 0.32142857142857145 | test_get_foreign_task_returns_404(), test_get_task_returns_own_task(), test_get_unknown_task_returns_404(), anyio |
| Gitflow и доставка изменений | 8 | 0.25 | Gitflow и доставка изменений, Conventional Commits на английском, develop: интеграционная ветка разработки, Новый PR создаётся черновиком |
| Валидация локального времени | 7 | 0.2857142857142857 | .serialize_local_time(), validate_local_time_format(), time, re |
| Тесты сервиса авторизации | 7 | 0.2857142857142857 | test_auth_service.py, test_refresh_raises_user_not_found_when_session_user_is_missing(), types, unittest_mock |
| Чтение access cookie | 6 | 0.3333333333333333 | get_access_token_cookie(), ACCESS_COOKIE_NAME, alias, Cookie |
| Создание и ответы проектов | 6 | 0.4 | create_project(), _project_detail_response(), ProjectDetailResponse, Добавляет колонки проекта к его агрегатам. |
| Health и CORS-тесты | 6 | 0.4 | test_cors_preflight_allows_local_frontend(), test_health_check_returns_ok(), anyio, AsyncClient |
| Базовый HTTP test client | 6 | 0.3333333333333333 | client(), anyio_backend(), fixture, AsyncClient |
| Тесты дедлайнов Сегодня | 6 | 0.4 | test_soon_deadline_includes_next_three_days_without_today(), test_today_deadline_has_priority_over_inbox(), anyio, AsyncClient |
| Команды локальной разработки | 6 | 0.3333333333333333 | Taskfile: команды разработки, Docker app profile: PostgreSQL и backend, backend:check: Ruff, formatting, mypy и pytest, Frontend check и build |
| Миграция таблиц задач | 5 | 0.4 | 202609030001_create_task_tables.py, upgrade(), downgrade(), Удаляет таблицу задач и справочник статусов. |
| Миграция таблиц проектов | 5 | 0.4 | 202609180001_add_projects.py, upgrade(), downgrade(), Удаляет проектные поля, колонки и проекты. |
| Endpoint dev-сброса пароля | 5 | 0.4 | reset_password(), Depends, post, Response |
| Docker и локальная инфраструктура | 5 | 0.6 | Docker Compose: локальное окружение, Backend контейнер app profile, Backend ждёт PostgreSQL service_healthy, PostgreSQL 17 Alpine с persistent volume |
| Макет архива задач | 5 | 0.4 | Archive: desktop UI reference, Действия: вернуть задачу и удалить, Поиск по архиву, фильтры и сортировка, Архив: задачи, план, дедлайн и время архивации |
| Макет календаря месяца | 5 | 0.4 | Calendar month: desktop UI reference, Неделя/Месяц, сегодня и переход к дате, Выбранный день: задачи по времени и без времени, Дедлайны и повторения выбранного дня |
| Макет календаря недели | 5 | 0.4 | Calendar week: desktop UI reference, Выбранный день: время, дедлайны и повторения, Красные карточки дедлайнов, Повторяющиеся задачи с частотой |
| Исторический макет входящих | 5 | 0.4 | Inbox: historical desktop UI reference, Поиск по задачам и сортировка, Видимые фильтры todo, done и archived в макете, Таблица задач: статус, дедлайн и обновлено |
| Макет входа | 5 | 0.4 | Login: desktop UI reference, Создать аккаунт и сбросить пароль: ссылки макета, Вход через логин и пароль, Личный план задач без лишнего шума |
| Исторический макет новой задачи | 5 | 0.4 | New task: historical desktop UI reference, План и дедлайн с датой и временем, Повторение задачи, Активная, выполненная и архивная: варианты макета |
| Макет планирования задач | 5 | 0.4 | Planning: desktop UI reference, Просрочка красная, близкие дедлайны оранжевые, Быстрые фильтры: сегодня, завтра, неделя, без даты и все, Частота повторения рядом с названием задачи |
| Макет регистрации | 5 | 0.4 | Register: desktop UI reference, Переход в существующий аккаунт, Ваши данные: только ваши, Планируйте день по-своему |
| Макет деталей задачи | 5 | 0.4 | Task details: desktop UI reference, Детали задачи: описание, статус и даты, Детали открыты поверх Планирования, Редактировать, выполнить, архивировать и удалить |
| Макет экрана Сегодня | 5 | 0.4 | Today: desktop UI reference, Требуют внимания: дедлайны и просрочка, Входящие и скоро дедлайн, Сводка: сегодня, входящие, дедлайны, просрочено и выполнено |
| Макет списка проектов | 5 | 0.4 | All projects: desktop UI reference, Новый проект и открытие проекта, Навигационные группы Задачи и Проекты, Карточки личных проектов с прогрессом выполнения |
| Макет создания проекта | 5 | 0.4 | New project: desktop UI reference, Этапы можно изменить в настройках проекта, Стандартные этапы: Бэклог, К выполнению, В работе, На проверке, Готово, Создание проекта поверх списка проектов |
| Макет новой проектной задачи | 5 | 0.4 | New project task: desktop UI reference, План, дедлайн и повторение, Выбор проекта и этапа, Новая проектная задача: название и описание |
| Макет Kanban-доски проекта | 5 | 0.4 | Project board: desktop UI reference, Доска/Список, поиск, даты, фильтры и порядок, Готово: задачи с зелёным индикатором выполнения, Перетаскивание карточки и placeholder |
| Макет списка проектных задач | 5 | 0.4 | Project list: desktop UI reference, Массовый перенос в этап и отметка выполненными, Готовые задачи с зачёркнутыми названиями, Доска/Список, поиск, даты, фильтры и порядок |
| Макет настроек проекта | 5 | 0.4 | Project settings: desktop UI reference, Колонки: порядок перетаскиванием, цвета и добавление, Готово: колонка завершает задачу, Архив сохраняет задачи, удаление требует подтверждения |
| Сериализация времени task views | 4 | 0.5 | .serialize_local_time(), field_serializer, time, Сериализует локальное время без секунд. |
| Тест доступа к Сегодня | 4 | 0.5 | test_today_view_rejects_request_without_access_token(), anyio, AsyncClient, Экран Сегодня требует авторизацию. |
| Тест справочника статусов | 4 | 0.5 | test_list_task_statuses_returns_active_statuses(), anyio, AsyncClient, Endpoint статусов возвращает активный системный справочник. |
| Валидация зависимости дедлайна | 3 | 0.6666666666666666 | .validate_deadline_time_dependency(), Не разрешает время дедлайна без даты дедлайна., model_validator |
| HTML entry приложения | 3 | 0.6666666666666666 | Frontend HTML entry, DOM root и module script /src/main.tsx, HTML lang=ru и responsive viewport |
| Связи TypeScript-конфигураций | 3 | 0.6666666666666666 | tsconfig.json, files, references |
| Индекс настроек backend | 2 | 1.0 | core/__init__.py, Базовые настройки и утилиты backend. |
| Индекс слоя БД | 2 | 1.0 | db/__init__.py, Работа с базой данных. |
| Индекс доменных значений | 2 | 1.0 | domain/__init__.py, Доменные значения и правила backend-модулей. |
| Индекс внутренних DTO | 2 | 1.0 | dto/__init__.py, Внутренние DTO backend-слоев. |
| Индекс доменных исключений | 2 | 1.0 | exceptions/__init__.py, Доменные исключения приложения. |
| Entry point backend | 2 | 1.0 | backend/__init__.py, main() |
| Индекс repository-слоя | 2 | 1.0 | repositories/__init__.py, Repository-слой для работы с хранилищем данных. |
| Индекс service-слоя | 2 | 1.0 | services/__init__.py, Service-слой с бизнес-логикой приложения. |
| Индекс валидаторов | 2 | 1.0 | validators/__init__.py, Валидаторы бизнес-правил. |
| Индекс интеграционных тестов | 2 | 1.0 | integration/__init__.py, Integration tests backend. |
| Shell-создание тестовой БД | 2 | 1.0 | create-test-db.sh script, create-test-db.sh |
| Пустой README backend | 1 | 1.0 | Backend README (пустой документ) |
| Индекс API-слоя | 1 | 1.0 | api/__init__.py |
| Индекс API v1 | 1 | 1.0 | v1/__init__.py |
| Индекс HTTP-схем | 1 | 1.0 | schemas/__init__.py |
| Индекс backend-тестов | 1 | 1.0 | tests/__init__.py |
| Python manifest backend | 1 | 1.0 | backend |
| PowerShell-создание тестовой БД | 1 | 1.0 | create-test-db.ps1 |

## Циклы импортов

- Детектор не обнаружил циклов импортов.

## Использование

- Откройте `graph.html` в браузере для интерактивной навигации. Визуализатор использует внешнюю библиотеку vis-network с CDN; для её загрузки нужен интернет.
- `graph.json` содержит узлы, связи, группы, источники и степень достоверности.
- `graphify query "TaskService"`, `graphify explain "TaskRepository"` и `graphify path "TaskService" "TaskRepository"` помогают исследовать граф.
- После изменений кода используйте `graphify update .`; после изменений документов или макетов повторите семантический анализ через навык graphify.
- `graphify-out/` создан в рабочем дереве. Публикуются граф, HTML и отчёт; кэш, manifest.json, cost.json и пути интерпретатора исключены локальным `.gitignore`.
- Продуктовое поведение, API и архитектура приложения не изменены; обновление Notion для этой карты не требуется.
