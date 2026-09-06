import { CalendarDays, Check, ShieldCheck, Target, Zap } from "lucide-react";
import { Outlet, useLocation } from "react-router";

type AuthVariant = "login" | "register";

function getAuthVariant(pathname: string): AuthVariant {
  return pathname === "/register" ? "register" : "login";
}

function LoginInfo() {
  return (
    <>
      <span className="brand-mark brand-mark--large" aria-hidden="true">
        <Check size={34} strokeWidth={3} />
      </span>
      <div className="auth-info__title-row">
        <h2>Daily Organizer</h2>
        <span className="version-badge">v0.1</span>
      </div>
      <p>Личный план задач без лишнего шума</p>
      <div className="auth-info__divider" />
      <ul className="auth-benefits">
        <li>
          <span aria-hidden="true">
            <Check size={20} strokeWidth={2.5} />
          </span>
          <div>
            <strong>Фокус на главном</strong>
            <p>Все, что нужно для продуктивного дня.</p>
          </div>
        </li>
        <li>
          <span aria-hidden="true">
            <CalendarDays size={20} strokeWidth={2.3} />
          </span>
          <div>
            <strong>Планируйте просто</strong>
            <p>Список задач, дедлайны и статус без лишнего.</p>
          </div>
        </li>
        <li>
          <span aria-hidden="true">
            <Zap size={20} strokeWidth={2.3} />
          </span>
          <div>
            <strong>Двигайтесь каждый день</strong>
            <p>Маленькие шаги приводят к большим результатам.</p>
          </div>
        </li>
      </ul>
      <p className="auth-info__footer">© 2026 Daily Organizer</p>
    </>
  );
}

function RegisterInfo() {
  return (
    <>
      <span className="brand-mark brand-mark--muted brand-mark--large" aria-hidden="true">
        <Check size={34} strokeWidth={3} />
      </span>
      <h2>Планируйте день по-своему</h2>
      <p>Простой и понятный планировщик задач, который помогает фокусироваться на важном.</p>
      <ul className="auth-benefits">
        <li>
          <span aria-hidden="true">
            <CalendarDays size={20} strokeWidth={2.3} />
          </span>
          <div>
            <strong>Все под контролем</strong>
            <p>Создавайте задачи, планируйте и отмечайте выполненное без лишних сложностей.</p>
          </div>
        </li>
        <li>
          <span aria-hidden="true">
            <Target size={20} strokeWidth={2.3} />
          </span>
          <div>
            <strong>Фокус на главном</strong>
            <p>Ясный список задач помогает не отвлекаться и достигать целей.</p>
          </div>
        </li>
        <li>
          <span aria-hidden="true">
            <ShieldCheck size={20} strokeWidth={2.3} />
          </span>
          <div>
            <strong>Ваши данные — только ваши</strong>
            <p>Никакого лишнего. Только вы и ваши задачи.</p>
          </div>
        </li>
      </ul>
    </>
  );
}

export function AuthLayout() {
  const { pathname } = useLocation();
  const variant = getAuthVariant(pathname);
  const isRegister = variant === "register";

  return (
    <main className={`auth-page auth-page--${variant}`}>
      <div className="auth-page__stage">
        <div className="auth-page__form-pane">
          <section className={`auth-card auth-card--${variant}`} aria-labelledby={`${variant}-title`}>
            <div
              className={
                isRegister ? "auth-card__header auth-card__header--center" : "auth-card__header"
              }
            >
              <span className="brand-mark" aria-hidden="true">
                <Check size={26} strokeWidth={3} />
              </span>
              <div>
                <div className="auth-card__brand-row">
                  <span className="auth-card__brand">Daily Organizer</span>
                  <span className="version-badge">v0.1</span>
                </div>
                <p className="auth-card__subtitle">Личный план задач без лишнего шума</p>
              </div>
            </div>
            {isRegister ? <div className="auth-card__divider" /> : null}
            <Outlet />
          </section>
        </div>

        <aside className={`auth-info auth-info--${variant}`} aria-label="О Daily Organizer">
          {isRegister ? <RegisterInfo /> : <LoginInfo />}
        </aside>
      </div>
    </main>
  );
}
