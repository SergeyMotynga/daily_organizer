import { Folder, MoreHorizontal } from "lucide-react";
import { Outlet, useLocation } from "react-router";
import { Brand, ThemeToggle } from "../../shared/ui/brand";

export function AuthLayout() {
  const isRegister = useLocation().pathname === "/register";
  return <div className={`route-auth${isRegister ? " route-auth--register" : ""}`}>
    <header className="route-topbar"><Brand /><ThemeToggle /></header>
    <main className="route-auth__body">
      <section className="route-auth__intro" aria-label="О Daily Organizer">
        <Brand hero />
        <h2>{isRegister ? <>Освободите место<br />для важного</> : <>Планы становятся<br />делами</>}</h2>
        <p>{isRegister ? <>Задачи, проекты и планы — в одном<br />спокойном пространстве.</> : <>Спокойное место для задач, проектов<br />и вашего дня.</>}</p>
        <div className="route-auth__preview" aria-label="Пример плана на день">
          {[
            { time: "09:30", title: "Читать 20 минут", project: "Личное · Ежедневно" },
            { time: "14:00", title: "Написать тесты авторизации", project: "Daily Organizer" },
            { time: "18:30", title: "Английский 15 минут", project: "Личное · По будням" }
          ].map((task, index) => <div className={`route-auth__example${index === 1 ? " route-auth__example--selected" : ""}`} key={task.time}><span>{task.time}</span><span className="route-auth__circle" aria-hidden="true" /><div><strong>{task.title}</strong><small><Folder size={16} aria-hidden="true" />{task.project}</small></div><MoreHorizontal size={22} aria-hidden="true" /></div>)}
        </div>
      </section>
      <section className="route-auth__form-pane" aria-label={isRegister ? "Регистрация" : "Вход"}>
        <div className="route-auth__form"><Outlet /></div>
        <footer>© 2026 Daily Organizer</footer>
      </section>
    </main>
  </div>;
}
