export const appRoutePaths = {
  tasks: {
    today: "/app/tasks/today",
    planning: "/app/tasks/planning",
    calendar: "/app/tasks/calendar",
    archive: "/app/tasks/archive"
  },
  projects: {
    all: "/app/projects",
    board: (projectId: string) => `/app/projects/${projectId}/board`,
    list: (projectId: string) => `/app/projects/${projectId}/list`
  }
} as const;
