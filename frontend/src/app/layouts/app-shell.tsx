import { useEffect, useRef, useState } from "react";
import { Archive, Calendar, CalendarDays, CalendarRange, Check, ChevronDown, LogOut } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router";

import { useCurrentUserQuery, useLogoutMutation } from "../../features/auth/session";

const navigationItems = [
  { to: "/app/today", label: "Сегодня", icon: CalendarDays },
  { to: "/app/planning", label: "Планирование", icon: CalendarRange },
  { to: "/app/calendar", label: "Календарь", icon: Calendar },
  { to: "/app/archive", label: "Архив", icon: Archive }
];

export function AppShell() {
  const navigate = useNavigate();
  const currentUserQuery = useCurrentUserQuery();
  const logoutMutation = useLogoutMutation();
  const user = currentUserQuery.data;
  const displayName = user?.name || user?.login || "Пользователь";
  const initials = displayName.slice(0, 2).toUpperCase();
  const [accountOpen, setAccountOpen] = useState(false);
  const accountRef = useRef<HTMLDivElement>(null);
  const accountToggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!accountOpen) return;

    function closeOutside(event: PointerEvent | FocusEvent) {
      if (!accountRef.current?.contains(event.target as Node)) {
        setAccountOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setAccountOpen(false);
        accountToggleRef.current?.focus({ preventScroll: true });
      }
    }

    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("focusin", closeOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("focusin", closeOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [accountOpen]);

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
            <Check size={28} strokeWidth={3} />
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
              <Icon size={21} strokeWidth={1.9} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="app-shell__account" ref={accountRef}>
          <div className="app-shell__avatar" aria-hidden="true">
            {initials}
          </div>
          <div className="app-shell__user">
            <strong>{displayName}</strong>
            {user?.login ? <span>{user.login}</span> : null}
          </div>
          <button
            className="app-shell__account-toggle"
            ref={accountToggleRef}
            aria-label="Меню аккаунта"
            aria-expanded={accountOpen}
            aria-controls="account-actions"
            onClick={() => setAccountOpen((open) => !open)}
            type="button"
          >
            <ChevronDown size={18} aria-hidden="true" />
          </button>
          <div
            id="account-actions"
            className={`app-shell__account-menu${accountOpen ? " app-shell__account-menu--open" : ""}`}
            aria-hidden={!accountOpen}
            inert={!accountOpen}
          >
            <button
              className="app-shell__logout"
              disabled={logoutMutation.isPending}
              onClick={handleLogout}
              type="button"
            >
              <LogOut size={17} aria-hidden="true" />
              <span>{logoutMutation.isPending ? "Выходим…" : "Выйти"}</span>
            </button>
          </div>
        </div>
      </aside>
      <main className="app-shell__content">
        <Outlet />
      </main>
    </div>
  );
}
