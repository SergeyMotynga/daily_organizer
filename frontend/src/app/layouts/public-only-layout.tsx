import { Navigate, Outlet } from "react-router";

import { isUnauthorizedError, useCurrentUserQuery } from "../../features/auth/session";
import { appRoutePaths } from "../route-paths";

export function PublicOnlyLayout() {
  const currentUserQuery = useCurrentUserQuery();
  const hasCachedUser = Boolean(currentUserQuery.data);
  const isInitialSessionCheck = currentUserQuery.isPending && !hasCachedUser;

  if (isInitialSessionCheck) {
    return <div className="page-state">Проверяем сессию...</div>;
  }

  if (hasCachedUser) {
    return <Navigate to={appRoutePaths.tasks.today} replace />;
  }

  if (isUnauthorizedError(currentUserQuery.error) || !currentUserQuery.data) {
    return <Outlet />;
  }

  return <Outlet />;
}
