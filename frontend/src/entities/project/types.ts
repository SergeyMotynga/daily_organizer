export type ProjectColumn = {
  id: string;
  project_id: string;
  title: string;
  position: number;
  is_completion_column: boolean;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: string;
  title: string;
  description: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
  task_count: number;
  completed_task_count: number;
  progress_percent: number;
};

export type ProjectDetail = Project & {
  columns: ProjectColumn[];
};

export type ProjectListResponse = {
  items: Project[];
};

export type CreateProjectPayload = {
  title: string;
  description: string | null;
};

export type UpdateProjectPayload = Partial<CreateProjectPayload> & {
  archived?: boolean;
};

export type UpdateProjectColumnPayload = {
  title?: string;
  is_completion_column?: boolean;
};
