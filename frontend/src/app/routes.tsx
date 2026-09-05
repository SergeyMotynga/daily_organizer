import { Navigate, Route, Routes } from "react-router";

import { AppShell } from "./layouts/app-shell";
import { ProtectedLayout } from "./layouts/protected-layout";
import { PublicOnlyLayout } from "./layouts/public-only-layout";
import { ArchivePage } from "../pages/archive-page";
import { LoginPage } from "../pages/login-page";
import { PlanningPage } from "../pages/planning-page";
import { RegisterPage } from "../pages/register-page";
import { TodayPage } from "../pages/today-page";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app/today" replace />} />
      <Route element={<PublicOnlyLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route element={<ProtectedLayout />}>
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Navigate to="/app/today" replace />} />
          <Route path="today" element={<TodayPage />} />
          <Route path="planning" element={<PlanningPage />} />
          <Route path="archive" element={<ArchivePage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/app/today" replace />} />
    </Routes>
  );
}
