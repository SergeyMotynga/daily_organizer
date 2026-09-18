import { useMemo, useState } from "react";
import { Clock3, Folder, Plus, RefreshCcw, Search } from "lucide-react";
import { useNavigate } from "react-router";

import { CreateProjectDrawer } from "../features/projects/create-project-drawer";
import { useProjectsQuery, useUpdateProjectMutation } from "../features/projects/queries";
import { SelectCombobox } from "../shared/ui/select-combobox";
import { appRoutePaths } from "../app/route-paths";

function formatUpdatedAt(value: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function RestoreButton({ projectId }: { projectId: string }) {
  const mutation = useUpdateProjectMutation(projectId);
  return <button type="button" onClick={() => mutation.mutate({ archived: false })} disabled={mutation.isPending}><RefreshCcw size={16} />{mutation.isPending ? "Восстанавливаем…" : "Восстановить"}</button>;
}

export function ProjectsPage() {
  const navigate = useNavigate();
  const [archived, setArchived] = useState(false);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("updated_desc");
  const [createOpen, setCreateOpen] = useState(false);
  const projectsQuery = useProjectsQuery(archived, query);
  const projects = useMemo(() => {
    const items = [...(projectsQuery.data?.items ?? [])];
    if (sort === "title_asc") items.sort((a, b) => a.title.localeCompare(b.title, "ru"));
    if (sort === "progress_desc") items.sort((a, b) => b.progress_percent - a.progress_percent);
    if (sort === "updated_asc") items.sort((a, b) => a.updated_at.localeCompare(b.updated_at));
    return items;
  }, [projectsQuery.data, sort]);

  return <div className="projects-page">
    <header className="projects-page__header">
      <div><h1>Все проекты</h1><p>Личные проекты и задачи по этапам</p></div>
      <button className="projects-primary-button" type="button" onClick={() => setCreateOpen(true)}><Plus size={19} />Новый проект</button>
    </header>
    <div className="projects-toolbar">
      <label className="projects-search"><Search size={20} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Поиск по проектам" /></label>
      <div className="projects-tabs" role="tablist"><button type="button" className={!archived ? "active" : ""} onClick={() => setArchived(false)}>Активные</button><button type="button" className={archived ? "active" : ""} onClick={() => setArchived(true)}>Архивные</button></div>
      <SelectCombobox className="projects-sort" label="Сортировка проектов" value={sort} onChange={setSort} options={[{ value: "updated_desc", label: "Сначала новые" }, { value: "updated_asc", label: "Сначала старые" }, { value: "title_asc", label: "По названию" }, { value: "progress_desc", label: "По прогрессу" }]} />
    </div>
    {projectsQuery.isPending ? <div className="projects-state">Загружаем проекты…</div> : null}
    {projectsQuery.isError ? <div className="projects-state projects-state--error"><strong>Не удалось загрузить проекты</strong><button type="button" onClick={() => void projectsQuery.refetch()}>Повторить</button></div> : null}
    {!projectsQuery.isPending && !projectsQuery.isError && projects.length === 0 ? <div className="projects-state"><Folder size={36} /><strong>{archived ? "Архивных проектов нет" : "Проектов пока нет"}</strong><p>{query ? "Измените поисковый запрос." : "Создайте первый проект и разложите задачи по этапам."}</p></div> : null}
    <div className="projects-grid">
      {projects.map((project) => <article className="project-card" key={project.id}>
        <div className="project-card__heading"><span><Folder size={27} /></span><div><h2>{project.title}</h2><p>{project.description || "Без описания"}</p></div></div>
        <div className="project-card__progress"><div><span style={{ width: `${project.progress_percent}%` }} /></div><strong>{project.progress_percent}%</strong></div>
        <p className="project-card__count">Выполнено {project.completed_task_count} из {project.task_count}</p>
        <footer><span><Clock3 size={16} />{formatUpdatedAt(project.updated_at)}</span>{archived ? <RestoreButton projectId={project.id} /> : <button type="button" onClick={() => navigate(appRoutePaths.projects.board(project.id))}>Открыть проект</button>}</footer>
      </article>)}
    </div>
    {createOpen ? <CreateProjectDrawer onClose={() => setCreateOpen(false)} /> : null}
  </div>;
}
