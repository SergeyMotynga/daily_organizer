import { useEffect, useRef, useState } from "react";
import { ChevronDown, LogOut, Settings } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { useCurrentUserQuery, useLogoutMutation } from "../../features/auth/session";
import { Brand, ThemeToggle } from "../../shared/ui/brand";
import { appRoutePaths } from "../route-paths";

const navigation = [
  { to: appRoutePaths.tasks.today, label: "Сегодня" },
  { to: appRoutePaths.tasks.planning, label: "Задачи" },
  { to: appRoutePaths.tasks.calendar, label: "Календарь" },
  { to: appRoutePaths.projects.all, label: "Проекты" },
  { to: appRoutePaths.tasks.archive, label: "Архив" }
];

export function AppShell() {
  const navigate = useNavigate();
  const user = useCurrentUserQuery().data;
  const logoutMutation = useLogoutMutation();
  const displayName = user?.name || user?.login || "Пользователь";
  const [accountOpen, setAccountOpen] = useState(false);
  const accountRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!accountOpen) return;
    function closeOutside(event: PointerEvent | FocusEvent) {
      if (!accountRef.current?.contains(event.target as Node)) setAccountOpen(false);
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setAccountOpen(false);
        toggleRef.current?.focus();
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
    try { await logoutMutation.mutateAsync(); }
    finally { navigate("/login", { replace: true }); }
  }

  return <div className="route-shell">
    <a className="skip-link" href="#main-content">К содержимому</a>
    <header className="route-topbar">
      <Brand />
      <nav className="route-navigation" aria-label="Основная навигация">
        {navigation.map(({ to, label }) => <NavLink key={to} to={to}>{label}</NavLink>)}
      </nav>
      <div className="route-account" ref={accountRef}>
        <ThemeToggle />
        <button ref={toggleRef} className="route-account__toggle" type="button" aria-label={`Аккаунт: ${displayName}`} aria-expanded={accountOpen} aria-controls="account-panel" onClick={() => setAccountOpen(!accountOpen)}>
          <span className="route-avatar" aria-hidden="true">{displayName.slice(0, 2).toUpperCase()}</span>
          <ChevronDown size={18} aria-hidden="true" />
        </button>
        <button className="route-settings" type="button" aria-label="Меню аккаунта" aria-expanded={accountOpen} onClick={() => setAccountOpen(!accountOpen)}><Settings size={27} aria-hidden="true" /></button>
        {accountOpen ? <div className="route-account__panel" id="account-panel">
          <strong>{displayName}</strong><span>{user?.login}</span>
          <button type="button" onClick={() => void handleLogout()} disabled={logoutMutation.isPending}><LogOut size={18} aria-hidden="true" />{logoutMutation.isPending ? "Выходим…" : "Выйти"}</button>
        </div> : null}
      </div>
    </header>
    <main className="route-content" id="main-content" tabIndex={-1}><Outlet /></main>
  </div>;
}
