import { Link } from "react-router";

export function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__panel">
        <p className="page-kicker">Авторизация</p>
        <h1>Регистрация</h1>
        <p>Здесь будет форма регистрации для v0.1.</p>
        <Link to="/login">Войти</Link>
      </section>
    </main>
  );
}
