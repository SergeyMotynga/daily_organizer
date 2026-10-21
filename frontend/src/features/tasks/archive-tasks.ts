import type { Task, TaskListResponse, TaskSort } from "../../entities/task/types";

export type ArchiveSort = TaskSort | "archived_at_desc" | "archived_at_asc";

export async function loadArchiveCollection(loadPage: (offset: number) => Promise<TaskListResponse>): Promise<Task[]> {
  const items: Task[] = [];
  let total = 0;
  do {
    const page = await loadPage(items.length);
    items.push(...page.items);
    total = page.pagination.total;
    if (!page.items.length) break;
  } while (items.length < total);
  return items;
}

export function paginateArchive(items: Task[], sort: ArchiveSort, limit: number, offset: number): TaskListResponse {
  const sorted = [...items];
  if (sort.startsWith("archived_at")) {
    sorted.sort((a,b) => sort === "archived_at_asc"
      ? (a.archived_at ?? "").localeCompare(b.archived_at ?? "")
      : (b.archived_at ?? "").localeCompare(a.archived_at ?? ""));
  }
  return { items: sorted.slice(offset, offset + limit), pagination: { total: sorted.length, limit, offset } };
}
