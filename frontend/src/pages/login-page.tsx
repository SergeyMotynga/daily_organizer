import { Link } from "react-router";

export function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__panel">
        <p className="page-kicker">Авторизация</p>
        <h1>Вход</h1>
        <p>Здесь будет форма входа для v0.1.</p>
        <Link to="/register">Регистрация</Link>
      </section>
    </main>
  );
}
