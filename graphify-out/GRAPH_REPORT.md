# Graph Report - daily_organizer  (2026-10-21)

## Corpus Check
- 187 files · ~979,659 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 22 file(s) not represented in the graph (top: .toml 8, (none) 7, .css 4)

## Summary
- 2028 nodes · 5080 edges · 117 communities (79 shown, 38 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 428 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d40112d0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- exceptions/tasks.py
- TaskRepository
- utc_now
- v1/tasks.py
- tasks/queries.ts
- pytest
- routes.tsx
- AuthService
- task-details-drawer.tsx
- mockup.js
- archive-page.tsx
- register_user
- test_project_service.py
- auth_client
- calendar-page.tsx
- ProjectColumnUpdateData
- project-page.tsx
- User
- test_deadline_presets.py
- package.json
- handlers.py
- create_task
- get_task_service
- v1/projects.py
- ProjectRepository
- test_project_workflows.py
- index.ts
- test_create.py
- deps.py
- services/projects.py
- projects/queries.ts
- v1/auth.py
- TaskService
- compilerOptions
- PasswordValidator
- test_today_timezone.py
- test_dev_reset_password.py
- schemas/task_recurrence_types.py
- services/tasks.py
- compilerOptions
- dev_auth.py
- test_login_rejects_invalid_payload
- test_sessionmaker
- Обзор проекта Daily Organizer
- integration/conftest.py
- typing
- Daily Organizer v0.2: черновой план
- Правила работы с Codex
- 202608300001_create_auth_tables.py
- collections_abc
- test_register_rejects_invalid_payload
- Правила агентов Daily Organizer
- .change_password
- anyio
- test_create_task_rejects_inactive_recurrence_type
- Daily Organizer v0.1: завершённая функциональная версия
- task.py
- test_calendar_returns_range_items_and_recurrence_completions
- test_daily_recurrence_completion_is_scoped_to_occurrence_date
- test_delete_recurring_task_cascades_completion_history
- test_get_foreign_task_returns_404
- Gitflow и доставка изменений
- .refresh
- Индекс локальной документации
- schemas/task_statuses.py
- test_list_task_statuses_returns_active_statuses
- test_cors_preflight_allows_local_frontend
- client
- ProjectColumnCreateData
- Taskfile: команды разработки
- 202609030001_create_task_tables.py
- 202609180001_add_projects.py
- test_logout.py
- Docker Compose: локальное окружение
- Archive: desktop UI reference
- Calendar month: desktop UI reference
- Calendar week: desktop UI reference
- Inbox: historical desktop UI reference
- Login: desktop UI reference
- New task: historical desktop UI reference
- Planning: desktop UI reference
- Register: desktop UI reference
- Task details: desktop UI reference
- Today: desktop UI reference
- All projects: desktop UI reference
- New project: desktop UI reference
- New project task: desktop UI reference
- Project board: desktop UI reference
- Project list: desktop UI reference
- Project settings: desktop UI reference
- test_today_view_rejects_request_without_access_token
- TaskMoveData
- Frontend HTML entry
- tsconfig.json
- create-test-db.sh script
- Backend README (пустой документ)
- backend
- test_done_today_uses_completed_at_date
- test_today_view_excludes_archived_tasks
- Daily Organizer: README
- Daily Organizer — макеты Full HD

## God Nodes (most connected - your core abstractions)
1. `User` - 87 edges
2. `auth_client()` - 87 edges
3. `TaskService` - 77 edges
4. `create_task()` - 69 edges
5. `ProjectService` - 64 edges
6. `Task` - 57 edges
7. `get_current_user()` - 45 edges
8. `TaskStatusCode` - 40 edges
9. `TaskRepository` - 37 edges
10. `apiRequest()` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Слои API → service → repository/ORM` --semantically_similar_to--> `Слои API → service → repository/ORM`  [INFERRED] [semantically similar]
  AGENTS.md → docs/development/codex-working-rules.md
- `Daily Organizer: README` --references--> `Gitflow и доставка изменений`  [EXTRACTED]
  README.md → docs/development/git-flow.md
- `Daily Organizer: README` --references--> `Обзор проекта Daily Organizer`  [EXTRACTED]
  README.md → docs/project.md
- `Daily Organizer: README` --references--> `Daily Organizer v0.1: завершённая функциональная версия`  [EXTRACTED]
  README.md → docs/version/v0.1/README.md
- `Daily Organizer: README` --references--> `Daily Organizer v0.2: черновой план`  [EXTRACTED]
  README.md → docs/version/v0.2/plan.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Backend layer flow** — agents_api_layer, agents_service_layer, agents_repository_layer [EXTRACTED 1.00]
- **Task completion and archive model** — docs_version_v0_1_readme_task_status, docs_version_v0_1_readme_independent_archive, docs_version_v0_1_readme_recurrence_rule, docs_version_v0_1_readme_occurrence_completion [EXTRACTED 1.00]
- **Personal project task flow** — docs_version_v0_2_plan_personal_projects, docs_version_v0_2_plan_kanban_columns, docs_version_v0_2_plan_shared_task, docs_version_v0_2_plan_board_list [EXTRACTED 1.00]

## Communities (117 total, 38 thin omitted)

### Community 0 - "exceptions/tasks.py"
Cohesion: 0.14
Nodes (8): InvalidCalendarRangeError, InvalidTaskRecurrenceCompletionError, InvalidTaskTitleError, InvalidTimezoneError, TaskError, TaskNotFoundError, validate_calendar_range(), validate_task_title()

### Community 1 - "TaskRepository"
Cohesion: 0.07
Nodes (4): TaskSort, TaskListFilters, TaskRepository, TodayViewSummaryResult

### Community 2 - "utc_now"
Cohesion: 0.08
Nodes (12): get_settings(), create_access_token(), create_refresh_token(), decode_access_token(), hash_refresh_token(), utc_now(), verify_password(), test_me_rejects_access_token_for_unknown_user() (+4 more)

### Community 3 - "v1/tasks.py"
Cohesion: 0.05
Nodes (15): parse_csv_enum(), complete_task_recurrence(), create_task(), delete_task(), get_task(), list_tasks(), move_task(), uncomplete_task_recurrence() (+7 more)

### Community 4 - "tasks/queries.ts"
Cohesion: 0.09
Nodes (35): CalendarTask, CalendarTaskItem, CreateTaskPayload, Task, TaskDeadlinePreset, TaskListParams, TaskListPreset, TaskListResponse (+27 more)

### Community 5 - "pytest"
Cohesion: 0.06
Nodes (8): block_ids(), block_titles(), regular_block_ids(), test_planned_tasks_are_also_visible_in_attention_blocks(), test_today_view_groups_tasks_by_blocks(), test_today_view_splits_today_deadlines_by_time(), test_soon_deadline_includes_next_three_days_without_today(), test_today_deadline_has_priority_over_inbox()

### Community 6 - "routes.tsx"
Cohesion: 0.07
Nodes (43): App(), AppShell(), navigation, AuthLayout(), ProtectedLayout(), PublicOnlyLayout(), AppProviders(), appRoutePaths (+35 more)

### Community 7 - "AuthService"
Cohesion: 0.12
Nodes (10): get_access_token_cookie(), AuthError, DevEndpointDisabledError, InvalidCredentialsError, InvalidOldPasswordError, InvalidRefreshTokenError, LoginAlreadyExistsError, UnauthorizedError (+2 more)

### Community 8 - "task-details-drawer.tsx"
Cohesion: 0.10
Nodes (33): TaskRecurrenceTypeCode, TaskStatusCode, handleKeyDown(), handleKeyDown(), useProjectQuery(), useProjectsQuery(), CreateTaskDrawer(), handleKeyDown() (+25 more)

### Community 9 - "mockup.js"
Cohesion: 0.14
Nodes (46): agenda(), archive(), archiveRows, auth(), board(), boardCard(), boardData, btn() (+38 more)

### Community 10 - "archive-page.tsx"
Cohesion: 0.21
Nodes (9): ArchiveSort, ArchivePage(), ArchiveTaskRow(), formatDate(), formatDateTime(), sortOptions, InputGroup(), InputGroupAddon() (+1 more)

### Community 11 - "register_user"
Cohesion: 0.06
Nodes (23): test_dev_reset_password_updates_password_and_revokes_sessions(), test_logout_clears_cookies_and_revokes_refresh_session(), test_me_returns_current_user(), test_change_password_rejects_invalid_access_token(), test_change_password_rejects_invalid_payload(), test_change_password_rejects_request_without_access_token(), test_change_password_rejects_weak_new_password(), test_change_password_rejects_wrong_old_password() (+15 more)

### Community 12 - "test_project_service.py"
Cohesion: 0.12
Nodes (19): make_column(), make_project(), make_service(), make_task(), make_user(), test_bulk_move_and_bulk_status(), test_bulk_move_validation_and_rollback(), test_create_column_rolls_back_and_validates_title() (+11 more)

### Community 13 - "auth_client"
Cohesion: 0.11
Nodes (18): auth_client(), test_list_archived_tasks_preserves_execution_statuses(), test_list_tasks_applies_presets(), test_list_tasks_default_excludes_archived(), test_list_tasks_filters_by_dates(), test_list_tasks_filters_by_planned_range_and_prefers_exact_date(), test_list_tasks_filters_multiple_statuses(), test_list_tasks_paginates() (+10 more)

### Community 14 - "calendar-page.tsx"
Cohesion: 0.14
Nodes (23): CalendarViewResponse, getCalendarView(), calendarQueryKeys, useCalendarViewQuery(), getRecurrenceLabel(), addDays(), addMonths(), CalendarItemChip() (+15 more)

### Community 16 - "project-page.tsx"
Cohesion: 0.09
Nodes (48): useProjectTasksQuery(), useUpdateTaskMutation(), isTaskRecurring(), TaskDateFilters(), TaskDateFiltersProps, TaskInlineDetails(), TaskListItem(), TaskListItemProps (+40 more)

### Community 17 - "User"
Cohesion: 0.11
Nodes (3): ProjectColumn, User, ProjectService

### Community 18 - "test_deadline_presets.py"
Cohesion: 0.19
Nodes (6): test_deadline_preset_uses_user_timezone(), test_exact_deadline_date_has_priority_over_preset(), test_list_tasks_applies_deadline_presets(), test_list_tasks_rejects_invalid_deadline_preset_and_timezone(), test_overdue_preset_uses_deadline_time_today(), titles()

### Community 19 - "package.json"
Cohesion: 0.05
Nodes (39): dependencies, @daypicker/react, @dnd-kit/helpers, @dnd-kit/react, lucide-react, ogl, react, react-aria-components (+31 more)

### Community 20 - "handlers.py"
Cohesion: 0.08
Nodes (9): http_error_handler(), make_domain_error_handler(), handler(), make_json_safe(), register_exception_handlers(), validation_error_handler(), build_error_response(), ErrorSpec (+1 more)

### Community 21 - "create_task"
Cohesion: 0.12
Nodes (13): create_task(), test_archive_and_restore_preserve_status(), test_patch_description_to_null(), test_patch_planned_time_to_null(), test_patch_recurrence_to_none_deletes_completion_history(), test_patch_rejects_archived_status(), test_patch_rejects_internal_fields(), test_patch_rejects_invalid_final_deadline_and_recurring_status() (+5 more)

### Community 22 - "get_task_service"
Cohesion: 0.06
Nodes (15): get_task_service(), get_calendar_view(), list_task_recurrence_types(), list_task_statuses(), get_today_view(), _task_responses(), _today_view_response(), CalendarTaskItemResponse (+7 more)

### Community 23 - "v1/projects.py"
Cohesion: 0.05
Nodes (31): get_current_user(), get_project_service(), normalize_optional_query_text(), bulk_move_project_tasks(), bulk_set_project_task_status(), create_project(), create_project_column(), delete_project() (+23 more)

### Community 24 - "ProjectRepository"
Cohesion: 0.06
Nodes (5): ProjectCreateData, ProjectSummaryData, ProjectUpdateData, Project, ProjectRepository

### Community 25 - "test_project_workflows.py"
Cohesion: 0.17
Nodes (13): auth_client(), create_project(), create_task(), test_bulk_move_and_status_keep_tasks_consistent(), test_completion_reassignment_synchronizes_both_columns(), test_empty_column_lifecycle_and_completion_guards(), test_move_inside_column_normalizes_positions_and_clamps_target(), test_move_rejects_wrong_project_missing_task_and_column() (+5 more)

### Community 26 - "index.ts"
Cohesion: 0.14
Nodes (14): AppProvidersProps, getTodayView(), todayQueryKeys, useTodayViewQuery(), TodayViewBlocks, TodayViewResponse, TodayViewSummary, ApiError (+6 more)

### Community 27 - "test_create.py"
Cohesion: 0.13
Nodes (11): test_create_task_accepts_todo_status(), test_create_task_rejects_archived_status(), test_create_task_rejects_deadline_time_without_date(), test_create_task_rejects_planned_time_with_seconds(), test_create_task_rejects_unknown_status(), test_create_task_validates_recurrence(), test_create_task_validates_title(), test_create_task_with_deadline_time_and_recurrence() (+3 more)

### Community 28 - "deps.py"
Cohesion: 0.09
Nodes (4): UserSession, UserSessionRepository, UserRepository, AuthResult

### Community 29 - "services/projects.py"
Cohesion: 0.14
Nodes (11): InvalidProjectColumnOrderError, InvalidProjectColumnTitleError, InvalidProjectTitleError, InvalidTaskProjectError, ProjectColumnNotEmptyError, ProjectColumnNotFoundError, ProjectCompletionColumnRequiredError, ProjectError (+3 more)

### Community 30 - "projects/queries.ts"
Cohesion: 0.10
Nodes (38): CreateProjectPayload, Project, ProjectColumn, ProjectDetail, ProjectListResponse, UpdateProjectColumnPayload, UpdateProjectPayload, bulkMoveProjectTasks() (+30 more)

### Community 31 - "v1/auth.py"
Cohesion: 0.08
Nodes (11): clear_auth_cookies(), set_access_cookie(), set_auth_cookies(), get_auth_service(), change_password(), login(), logout(), me() (+3 more)

### Community 32 - "TaskService"
Cohesion: 0.06
Nodes (11): TaskRecurrenceTypeCode, TaskStatusCode, CalendarTaskItem, TaskCreateData, TaskUpdateData, InvalidTaskScheduleError, TaskRecurrenceTypeNotFoundError, TaskStatusNotFoundError (+3 more)

### Community 33 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 34 - "PasswordValidator"
Cohesion: 0.16
Nodes (5): WeakPasswordError, PasswordValidator, password_validator(), test_validate_new_password_accepts_valid_passwords(), test_validate_new_password_rejects_invalid_passwords()

### Community 35 - "test_today_timezone.py"
Cohesion: 0.17
Nodes (3): _local_datetime_utc(), test_done_today_uses_user_local_day(), test_today_view_rejects_invalid_timezone()

### Community 36 - "test_dev_reset_password.py"
Cohesion: 0.23
Nodes (4): test_dev_reset_password_is_disabled_outside_dev_mode(), test_dev_reset_password_rejects_invalid_payload(), test_dev_reset_password_rejects_unknown_user(), test_dev_reset_password_rejects_weak_password()

### Community 38 - "services/tasks.py"
Cohesion: 0.09
Nodes (8): TaskDeadlinePreset, TaskListPreset, PaginationParams, CalendarViewResult, TaskListQuery, TaskListItemResult, TaskListResult, TodayViewBlocksResult

### Community 39 - "compilerOptions"
Cohesion: 0.14
Nodes (13): compilerOptions, allowJs, isolatedModules, lib, module, moduleResolution, noEmit, resolveJsonModule (+5 more)

### Community 40 - "dev_auth.py"
Cohesion: 0.13
Nodes (6): reset_password(), ChangePasswordRequest, DevResetPasswordRequest, LoginRequest, RegisterRequest, trim()

### Community 41 - "test_login_rejects_invalid_payload"
Cohesion: 0.24
Nodes (4): test_login_rejects_invalid_payload(), test_login_rejects_unknown_login(), test_login_rejects_wrong_password(), test_login_sets_auth_cookies()

### Community 42 - "test_sessionmaker"
Cohesion: 0.23
Nodes (5): apply_test_migrations(), clean_data_tables(), client(), override_get_db(), test_sessionmaker()

### Community 43 - "Обзор проекта Daily Organizer"
Cohesion: 0.29
Nodes (4): Обзор проекта Daily Organizer, v0.7: MCP-интеграция как будущий слой, Первый клиент: адаптивное web-приложение, Roadmap: задачи, проекты, планы, отчёты, финансы, MCP

### Community 44 - "integration/conftest.py"
Cohesion: 0.20
Nodes (3): get_test_database_url(), get_test_migration_database_url(), test_engine()

### Community 45 - "typing"
Cohesion: 0.12
Nodes (3): get_db(), get_sessionmaker(), UserResponse

### Community 46 - "Daily Organizer v0.2: черновой план"
Cohesion: 0.21
Nodes (11): Канонические маршруты /app/tasks/* с legacy redirects, Представления проекта: Доска и Список, После проектов: Notes, hardening или deploy, Drag-and-drop: @dnd-kit/react и @dnd-kit/helpers, Daily Organizer v0.2: черновой план, Завершающая колонка синхронизирует status done, Настраиваемые колонки Kanban-доски, Личные проекты с одним владельцем (+3 more)

### Community 47 - "Правила работы с Codex"
Cohesion: 0.29
Nodes (3): Правила работы с Codex, Завершённая задача включает рабочую ветку и PR, Ревью: регрессии, безопасность и владельцы данных

### Community 48 - "202608300001_create_auth_tables.py"
Cohesion: 0.18
Nodes (4): downgrade(), upgrade(), downgrade(), upgrade()

### Community 49 - "collections_abc"
Cohesion: 0.18
Nodes (4): downgrade(), upgrade(), downgrade(), upgrade()

### Community 50 - "test_register_rejects_invalid_payload"
Cohesion: 0.24
Nodes (4): test_register_creates_user(), test_register_rejects_duplicate_login(), test_register_rejects_invalid_payload(), test_register_rejects_weak_password()

### Community 51 - "Правила агентов Daily Organizer"
Cohesion: 0.27
Nodes (8): API: HTTP mapping и зависимости, backend:check и backend:test-cov, Правила агентов Daily Organizer, Domain enums и reusable validators, Schemas: HTTP Pydantic schemas, DTO: внутренние dataclasses, Repository: запросы без commit/rollback, Service: бизнес-логика и транзакции

### Community 54 - "test_create_task_rejects_inactive_recurrence_type"
Cohesion: 0.24
Nodes (3): test_create_task_rejects_inactive_recurrence_type(), test_list_task_recurrence_types_requires_auth(), test_list_task_recurrence_types_returns_active_reference()

### Community 55 - "Daily Organizer v0.1: завершённая функциональная версия"
Cohesion: 0.27
Nodes (8): GET /api/v1/calendar: диапазон календаря, Daily Organizer v0.1: завершённая функциональная версия, task_recurrence_completions: выполнение на дату, Быстрые фильтры, даты, диапазон, статус, поиск и сортировка, PUT/DELETE recurrence-completions/{occurrence_date}, Повторяющаяся задача остаётся правилом в tasks, status_code: только todo и done, Today, Planning, Calendar и Archive

### Community 56 - "task.py"
Cohesion: 0.07
Nodes (8): get_migration_database_url(), run_migrations_offline(), run_migrations_online(), Base, CalendarRecurrenceCompletion, TaskRecurrenceCompletion, TaskRecurrenceType, TaskStatus

### Community 57 - "test_calendar_returns_range_items_and_recurrence_completions"
Cohesion: 0.25
Nodes (3): calendar_titles(), test_calendar_rejects_invalid_range(), test_calendar_returns_range_items_and_recurrence_completions()

### Community 58 - "test_daily_recurrence_completion_is_scoped_to_occurrence_date"
Cohesion: 0.33
Nodes (3): test_daily_recurrence_completion_is_scoped_to_occurrence_date(), test_weekdays_recurrence_is_hidden_on_weekend(), test_weekly_interval_and_archive_control_today_visibility()

### Community 60 - "test_get_foreign_task_returns_404"
Cohesion: 0.32
Nodes (3): test_get_foreign_task_returns_404(), test_get_task_returns_own_task(), test_get_unknown_task_returns_404()

### Community 61 - "Gitflow и доставка изменений"
Cohesion: 0.25
Nodes (6): Conventional Commits на английском, develop: интеграционная ветка разработки, Gitflow и доставка изменений, Новый PR создаётся черновиком, main: стабильная production-ветка, feature/ и bugfix/: ветки от origin/develop

### Community 63 - "Индекс локальной документации"
Cohesion: 0.18
Nodes (8): Задачи и даты, Клавиатура и адаптивность, Ошибки и границы, Подготовка, Проекты и доска, Чеклист проверки фронтенда, Индекс локальной документации, Miro: ссылка на схемы и UI v0.1

### Community 69 - "Taskfile: команды разработки"
Cohesion: 0.33
Nodes (6): Docker app profile: PostgreSQL и backend, backend:check: Ruff, formatting, mypy и pytest, Taskfile: команды разработки, Frontend check и build, Docker: PostgreSQL и тестовая база, backend:test-cov: pytest coverage

### Community 73 - "Docker Compose: локальное окружение"
Cohesion: 0.60
Nodes (4): Backend контейнер app profile, Docker Compose: локальное окружение, Локальные порты 127.0.0.1:5432 и 127.0.0.1:8000, PostgreSQL 17 Alpine с persistent volume

### Community 74 - "Archive: desktop UI reference"
Cohesion: 0.40
Nodes (5): Действия: вернуть задачу и удалить, Поиск по архиву, фильтры и сортировка, Архив: задачи, план, дедлайн и время архивации, Пагинация и размер страницы, Archive: desktop UI reference

### Community 75 - "Calendar month: desktop UI reference"
Cohesion: 0.40
Nodes (5): Неделя/Месяц, сегодня и переход к дате, Выбранный день: задачи по времени и без времени, Дедлайны и повторения выбранного дня, Месячная сетка с задачами по дням, Calendar month: desktop UI reference

### Community 76 - "Calendar week: desktop UI reference"
Cohesion: 0.40
Nodes (5): Выбранный день: время, дедлайны и повторения, Красные карточки дедлайнов, Повторяющиеся задачи с частотой, Calendar week: desktop UI reference, Недельные колонки: задачи без времени и временные карточки

### Community 77 - "Inbox: historical desktop UI reference"
Cohesion: 0.40
Nodes (5): Inbox: historical desktop UI reference, Поиск по задачам и сортировка, Видимые фильтры todo, done и archived в макете, Таблица задач: статус, дедлайн и обновлено, Входящие: задачи без плана

### Community 78 - "Login: desktop UI reference"
Cohesion: 0.40
Nodes (5): Создать аккаунт и сбросить пароль: ссылки макета, Вход через логин и пароль, Личный план задач без лишнего шума, Login: desktop UI reference, Оставаться в системе

### Community 79 - "New task: historical desktop UI reference"
Cohesion: 0.40
Nodes (5): План и дедлайн с датой и временем, Повторение задачи, New task: historical desktop UI reference, Активная, выполненная и архивная: варианты макета, Новая задача: боковая панель с названием и описанием

### Community 80 - "Planning: desktop UI reference"
Cohesion: 0.40
Nodes (5): Просрочка красная, близкие дедлайны оранжевые, Быстрые фильтры: сегодня, завтра, неделя, без даты и все, Частота повторения рядом с названием задачи, Planning: desktop UI reference, Таблица: задача, статус, план, дедлайн и обновлено

### Community 81 - "Register: desktop UI reference"
Cohesion: 0.40
Nodes (5): Переход в существующий аккаунт, Ваши данные: только ваши, Планируйте день по-своему, Register: desktop UI reference, Регистрация: имя, логин, пароль и повтор пароля

### Community 82 - "Task details: desktop UI reference"
Cohesion: 0.40
Nodes (5): Детали задачи: описание, статус и даты, Детали открыты поверх Планирования, Task details: desktop UI reference, Редактировать, выполнить, архивировать и удалить, Повторение, создано и обновлено

### Community 83 - "Today: desktop UI reference"
Cohesion: 0.40
Nodes (5): Требуют внимания: дедлайны и просрочка, Входящие и скоро дедлайн, Today: desktop UI reference, Сводка: сегодня, входящие, дедлайны, просрочено и выполнено, План на сегодня и выполнено сегодня

### Community 84 - "All projects: desktop UI reference"
Cohesion: 0.40
Nodes (5): Новый проект и открытие проекта, Навигационные группы Задачи и Проекты, Карточки личных проектов с прогрессом выполнения, Поиск, активные/архивные и сортировка, All projects: desktop UI reference

### Community 85 - "New project: desktop UI reference"
Cohesion: 0.40
Nodes (5): Этапы можно изменить в настройках проекта, Стандартные этапы: Бэклог, К выполнению, В работе, На проверке, Готово, Создание проекта поверх списка проектов, Новый проект: название и описание, New project: desktop UI reference

### Community 86 - "New project task: desktop UI reference"
Cohesion: 0.40
Nodes (5): План, дедлайн и повторение, Выбор проекта и этапа, Новая проектная задача: название и описание, New project task: desktop UI reference, Задача появится в Планировании и Календаре по датам

### Community 87 - "Project board: desktop UI reference"
Cohesion: 0.40
Nodes (5): Доска/Список, поиск, даты, фильтры и порядок, Готово: задачи с зелёным индикатором выполнения, Перетаскивание карточки и placeholder, Kanban-доска: пять этапов с карточками задач, Project board: desktop UI reference

### Community 88 - "Project list: desktop UI reference"
Cohesion: 0.40
Nodes (5): Массовый перенос в этап и отметка выполненными, Готовые задачи с зачёркнутыми названиями, Доска/Список, поиск, даты, фильтры и порядок, Список проектных задач с этапом, планом и дедлайном, Project list: desktop UI reference

### Community 89 - "Project settings: desktop UI reference"
Cohesion: 0.40
Nodes (5): Колонки: порядок перетаскиванием, цвета и добавление, Готово: колонка завершает задачу, Архив сохраняет задачи, удаление требует подтверждения, Project settings: desktop UI reference, Настройки проекта: название и описание

### Community 94 - "Frontend HTML entry"
Cohesion: 0.67
Nodes (3): Frontend HTML entry, DOM root и module script /src/main.tsx, HTML lang=ru и responsive viewport

### Community 116 - "Daily Organizer: README"
Cohesion: 0.33
Nodes (6): v0.1: daily-first to-do list, Daily Organizer: README, Локальный запуск backend/frontend с API proxy, Ссылка на Miro: схемы и UI v0.1, Ссылки на Notion: проект, ТЗ, фичлист, MCP draft, v0.2: структура приложения и личные проекты

### Community 117 - "Daily Organizer — макеты Full HD"
Cohesion: 0.40
Nodes (4): Daily Organizer — макеты Full HD, Как посмотреть, Основные решения, Что находится в папке

## Knowledge Gaps
- **104 isolated node(s):** `backend`, `@types/node`, `@types/react`, `@types/react-dom`, `typescript` (+99 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 946 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **38 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `TaskService`, `TaskRepository`, `v1/tasks.py`, `services/tasks.py`, `AuthService`, `test_project_service.py`, `.change_password`, `get_task_service`, `v1/projects.py`, `task.py`, `ProjectRepository`, `deps.py`, `services/projects.py`, `.refresh`, `v1/auth.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `User` (e.g. with `get_current_user()` and `change_password()`) actually correct?**
  _`User` has 39 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backend`, `@types/node`, `@types/react` to the rest of the system?**
  _104 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `exceptions/tasks.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13768115942028986 - nodes in this community are weakly interconnected._
- **Why does `auth_client()` connect `auth_client` to `test_list_task_statuses_returns_active_statuses`, `test_today_timezone.py`, `pytest`, `test_delete_recurring_task_cascades_completion_history`, `register_user`, `test_done_today_uses_completed_at_date`, `test_today_view_excludes_archived_tasks`, `test_deadline_presets.py`, `create_task`, `test_create_task_rejects_inactive_recurrence_type`, `task.py`, `test_calendar_returns_range_items_and_recurrence_completions`, `test_daily_recurrence_completion_is_scoped_to_occurrence_date`, `test_create.py`, `test_get_foreign_task_returns_404`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `TaskService` (e.g. with `get_calendar_view()` and `list_task_recurrence_types()`) actually correct?**
  _`TaskService` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Should `TaskRepository` be split into smaller, more focused modules?**
  _Cohesion score 0.06565656565656566 - nodes in this community are weakly interconnected._