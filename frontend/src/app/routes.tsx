import { Navigate, Route, Routes, useLocation } from "react-router";

import { AppShell } from "./layouts/app-shell";
import { AuthLayout } from "./layouts/auth-layout";
import { ProtectedLayout } from "./layouts/protected-layout";
import { PublicOnlyLayout } from "./layouts/public-only-layout";
import { appRoutePaths } from "./route-paths";
import { ArchivePage } from "../pages/archive-page";
import { CalendarPage } from "../pages/calendar-page";
import { LoginPage } from "../pages/login-page";
import { PlanningPage } from "../pages/planning-page";
import { RegisterPage } from "../pages/register-page";
import { TodayPage } from "../pages/today-page";
import { ProjectsPage } from "../pages/projects-page";
import { ProjectPage } from "../pages/project-page";

function LegacyTaskRouteRedirect({ to }: { to: string }) {
  const { search, hash } = useLocation();

  return <Navigate to={`${to}${search}${hash}`} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={appRoutePaths.tasks.today} replace />} />
      <Route element={<PublicOnlyLayout />}>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
      </Route>
      <Route element={<ProtectedLayout />}>
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Navigate to={appRoutePaths.tasks.today} replace />} />
          <Route path="tasks">
            <Route index element={<Navigate to={appRoutePaths.tasks.today} replace />} />
            <Route path="today" element={<TodayPage />} />
            <Route path="planning" element={<PlanningPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="archive" element={<ArchivePage />} />
          </Route>
          <Route path="projects">
            <Route index element={<ProjectsPage />} />
            <Route path=":projectId/board" element={<ProjectPage />} />
            <Route path=":projectId/list" element={<ProjectPage />} />
          </Route>
          <Route path="today" element={<LegacyTaskRouteRedirect to={appRoutePaths.tasks.today} />} />
          <Route path="planning" element={<LegacyTaskRouteRedirect to={appRoutePaths.tasks.planning} />} />
          <Route path="calendar" element={<LegacyTaskRouteRedirect to={appRoutePaths.tasks.calendar} />} />
          <Route path="archive" element={<LegacyTaskRouteRedirect to={appRoutePaths.tasks.archive} />} />
          <Route path="*" element={<Navigate to={appRoutePaths.tasks.today} replace />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to={appRoutePaths.tasks.today} replace />} />
    </Routes>
  );
}
