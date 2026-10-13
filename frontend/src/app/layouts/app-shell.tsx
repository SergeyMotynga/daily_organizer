import { useCallback, useEffect, useRef, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Archive,
  Calendar,
  CalendarDays,
  CalendarRange,
  Check,
  ChevronDown,
  Folder,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  X
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router";

import { useCurrentUserQuery, useLogoutMutation } from "../../features/auth/session";
import { useProjectsQuery } from "../../features/projects/queries";
import { appRoutePaths } from "../route-paths";

type NavigationGroup = {
  id: string;
  label: string;
  items: {
    to: string;
    label: string;
    icon: LucideIcon;
  }[];
};

const taskNavigationGroup: NavigationGroup =
  {
    id: "tasks",
    label: "Задачи",
    items: [
      { to: appRoutePaths.tasks.today, label: "Сегодня", icon: CalendarDays },
      { to: appRoutePaths.tasks.planning, label: "Планирование", icon: CalendarRange },
      { to: appRoutePaths.tasks.calendar, label: "Календарь", icon: Calendar },
      { to: appRoutePaths.tasks.archive, label: "Архив", icon: Archive }
    ]
  };

export function AppShell() {
  const navigate = useNavigate();
  const currentUserQuery = useCurrentUserQuery();
  const logoutMutation = useLogoutMutation();
  const projectsQuery = useProjectsQuery(false);
  const user = currentUserQuery.data;
  const displayName = user?.name || user?.login || "Пользователь";
  const initials = displayName.slice(0, 2).toUpperCase();
  const [accountOpen, setAccountOpen] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.matchMedia("(max-width: 760px)").matches);
  const accountRef = useRef<HTMLDivElement>(null);
  const accountToggleRef = useRef<HTMLButtonElement>(null);
  const mobileTriggerRef = useRef<HTMLButtonElement>(null);
  const navigationGroups: NavigationGroup[] = [
    taskNavigationGroup,
    {
      id: "projects",
      label: "Проекты",
      items: [
        { to: appRoutePaths.projects.all, label: "Все проекты", icon: Folder },
        ...(projectsQuery.data?.items.slice(0, 3).map((project) => ({
          to: appRoutePaths.projects.board(project.id),
          label: project.title,
          icon: Folder
        })) ?? [])
      ]
    }
  ];

  const closeMobileSidebar = useCallback(() => {
    setMobileOpen(false);
    window.requestAnimationFrame(() => mobileTriggerRef.current?.focus({ preventScroll: true }));
  }, []);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 760px)");

    function handleViewportChange(event: MediaQueryListEvent) {
      setIsMobile(event.matches);
      if (!event.matches) {
        setMobileOpen(false);
      }
    }

    mediaQuery.addEventListener("change", handleViewportChange);
    return () => mediaQuery.removeEventListener("change", handleViewportChange);
  }, []);

  useEffect(() => {
    function handleSidebarKeyboard(event: KeyboardEvent) {
      if (event.key === "Escape" && mobileOpen) {
        closeMobileSidebar();
      }
    }

    document.addEventListener("keydown", handleSidebarKeyboard);
    return () => document.removeEventListener("keydown", handleSidebarKeyboard);
  }, [closeMobileSidebar, mobileOpen]);

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
    <div
      className="app-shell"
      data-mobile-open={mobileOpen}
      data-sidebar-state={sidebarExpanded ? "expanded" : "collapsed"}
    >
      <button
        className="app-shell__mobile-overlay"
        aria-label="Закрыть боковую панель"
        onClick={closeMobileSidebar}
        tabIndex={mobileOpen ? 0 : -1}
        type="button"
      />
      <aside
        className="app-shell__sidebar"
        id="app-sidebar"
        aria-label="Основная навигация"
        aria-hidden={isMobile && !mobileOpen}
        inert={isMobile && !mobileOpen}
      >
        <div className="app-shell__brand">
          <span className="brand-mark" aria-hidden="true">
            <Check size={28} strokeWidth={3} />
          </span>
          <span className="app-shell__brand-copy">
            <span>Daily Organizer</span>
            <span className="version-badge">v0.2</span>
          </span>
        </div>
        <button
          className="app-shell__mobile-close"
          aria-label="Закрыть боковую панель"
          onClick={closeMobileSidebar}
          type="button"
        >
          <X size={19} aria-hidden="true" />
        </button>
        <nav className="app-shell__nav">
          {navigationGroups.map((group) => (
            <div className="app-shell__nav-group" aria-labelledby={`nav-group-${group.id}`} key={group.id}>
              <span className="app-shell__nav-label" id={`nav-group-${group.id}`}>
                {group.label}
              </span>
              <div className="app-shell__nav-list">
                {group.items.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    title={!isMobile && !sidebarExpanded ? label : undefined}
                    onClick={() => {
                      if (isMobile) closeMobileSidebar();
                    }}
                    className={({ isActive }) =>
                      isActive ? "app-shell__nav-link app-shell__nav-link--active" : "app-shell__nav-link"
                    }
                  >
                    <Icon size={21} strokeWidth={1.9} aria-hidden="true" />
                    <span>{label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
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
        <button
          className="app-shell__sidebar-toggle"
          aria-controls="app-sidebar"
          aria-expanded={sidebarExpanded}
          aria-label={sidebarExpanded ? "Свернуть боковую панель" : "Развернуть боковую панель"}
          onClick={() => setSidebarExpanded((expanded) => !expanded)}
          title={sidebarExpanded ? "Свернуть боковую панель" : "Развернуть боковую панель"}
          type="button"
        >
          {sidebarExpanded ? (
            <PanelLeftClose size={17} aria-hidden="true" />
          ) : (
            <PanelLeftOpen size={17} aria-hidden="true" />
          )}
        </button>
      </aside>
      <button
        className="app-shell__mobile-trigger"
        ref={mobileTriggerRef}
        aria-controls="app-sidebar"
        aria-expanded={mobileOpen}
        aria-label="Открыть боковую панель"
        onClick={() => setMobileOpen(true)}
        type="button"
      >
        <PanelLeftOpen size={20} aria-hidden="true" />
      </button>
      <main className="app-shell__content">
        <Outlet />
      </main>
    </div>
  );
}
