import { useState } from "react";
import { Moon, Sun } from "lucide-react";
import logoLight from "../../../../docs/design/ui-redesign/references/logo-light.svg";
import logoDark from "../../../../docs/design/ui-redesign/references/logo-dark.svg";

export function Brand({ hero = false }: { hero?: boolean }) {
  return <span className={hero ? "route-brand route-brand--hero" : "route-brand"}>
    <img className="route-logo route-logo--light" src={logoLight} alt="" width={hero ? 98 : 42} height={hero ? 98 : 42} />
    <img className="route-logo route-logo--dark" src={logoDark} alt="" width={hero ? 98 : 42} height={hero ? 98 : 42} />
    {!hero ? <span>Daily Organizer</span> : null}
  </span>;
}

export function ThemeToggle() {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme ?? "light");
  function toggleTheme() {
    const next = theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    setTheme(next);
    try { localStorage.setItem("daily-organizer-theme", next); } catch { /* Тема работает и без хранилища. */ }
  }
  return <button className="theme-toggle" type="button" aria-label={theme === "light" ? "Включить тёмную тему" : "Включить светлую тему"} onClick={toggleTheme}>
    {theme === "light" ? <Moon size={22} aria-hidden="true" /> : <Sun size={22} aria-hidden="true" />}
  </button>;
}
