import { Navigate, Outlet, useLocation } from "react-router";

import { isUnauthorizedError, useCurrentUserQuery } from "../../features/auth/session";

export function ProtectedLayout() {
  const location = useLocation();
  const currentUserQuery = useCurrentUserQuery();
  const hasCachedUser = Boolean(currentUserQuery.data);
  const isInitialSessionCheck = currentUserQuery.isPending && !hasCachedUser;

  if (isInitialSessionCheck) {
    return <div className="page-state">Проверяем сессию...</div>;
  }

  if (isUnauthorizedError(currentUserQuery.error) || !hasCachedUser) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
