import { Archive, CalendarDays, CalendarRange, Check, LogOut } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router";

import { useCurrentUserQuery, useLogoutMutation } from "../../features/auth/session";

const navigationItems = [
  { to: "/app/today", label: "Сегодня", icon: CalendarDays },
  { to: "/app/planning", label: "Планирование", icon: CalendarRange },
  { to: "/app/archive", label: "Архив", icon: Archive }
];

export function AppShell() {
  const navigate = useNavigate();
  const currentUserQuery = useCurrentUserQuery();
  const logoutMutation = useLogoutMutation();
  const user = currentUserQuery.data;
  const displayName = user?.name || user?.login || "Пользователь";
  const initials = displayName.slice(0, 2).toUpperCase();

  async function handleLogout() {
    try {
      await logoutMutation.mutateAsync();
    } finally {
      navigate("/login", { replace: true });
    }
  }

  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar" aria-label="Основная навигация">
        <div className="app-shell__brand">
          <span className="brand-mark" aria-hidden="true">
            <Check size={20} strokeWidth={3} />
          </span>
          <span>Daily Organizer</span>
          <span className="version-badge">v0.1</span>
        </div>
        <nav className="app-shell__nav">
          {navigationItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                isActive ? "app-shell__nav-link app-shell__nav-link--active" : "app-shell__nav-link"
              }
            >
              <Icon size={17} strokeWidth={1.9} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="app-shell__account">
          <div className="app-shell__avatar" aria-hidden="true">
            {initials}
          </div>
          <div className="app-shell__user">
            <strong>{displayName}</strong>
            {user?.login ? <span>{user.login}</span> : null}
          </div>
          <button
            className="app-shell__logout"
            disabled={logoutMutation.isPending}
            onClick={handleLogout}
            type="button"
          >
            <LogOut size={15} strokeWidth={2.2} />
            <span>{logoutMutation.isPending ? "..." : "Выйти"}</span>
          </button>
        </div>
      </aside>
      <main className="app-shell__content">
        <Outlet />
      </main>
    </div>
  );
}
