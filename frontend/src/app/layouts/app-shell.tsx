import { NavLink, Outlet } from "react-router";

const navigationItems = [
  { to: "/app/today", label: "Сегодня" },
  { to: "/app/planning", label: "Планирование" },
  { to: "/app/archive", label: "Архив" }
];

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar" aria-label="Основная навигация">
        <div className="app-shell__brand">Daily Organizer</div>
        <nav className="app-shell__nav">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "app-shell__nav-link app-shell__nav-link--active" : "app-shell__nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="app-shell__content">
        <Outlet />
      </main>
    </div>
  );
}
