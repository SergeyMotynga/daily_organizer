import { FormEvent, useState } from "react";
import { Eye, EyeOff, LockKeyhole, UserRound } from "lucide-react";
import { Link, useNavigate } from "react-router";

import { PrimaryButton } from "../features/auth/primary-button";
import { getAuthErrorMessage, useLoginMutation } from "../features/auth/session";
import { Checkbox } from "../shared/ui/checkbox";

type LoginFormErrors = {
  login?: string;
  password?: string;
};

function validateLoginForm(login: string, password: string): LoginFormErrors {
  const errors: LoginFormErrors = {};

  if (!login.trim()) {
    errors.login = "Введите логин.";
  }

  if (!password) {
    errors.password = "Введите пароль.";
  }

  return errors;
}

export function LoginPage() {
  const navigate = useNavigate();
  const loginMutation = useLoginMutation();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<LoginFormErrors>({});

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validateLoginForm(login, password);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    try {
      await loginMutation.mutateAsync({ login: login.trim(), password });
      navigate("/app/today", { replace: true });
    } catch {
      return;
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <h1 id="login-title">Вход в аккаунт</h1>

      <label className="form-field">
        <span className="form-field__label">Логин</span>
        <span className="auth-input">
          <span className="auth-input__icon" aria-hidden="true">
            <UserRound size={18} strokeWidth={2} />
          </span>
          <input
            aria-describedby={errors.login ? "login-error" : undefined}
            aria-invalid={Boolean(errors.login)}
            autoComplete="username"
            disabled={loginMutation.isPending}
            onChange={(event) => setLogin(event.target.value)}
            placeholder="Введите логин"
            value={login}
          />
        </span>
        {errors.login ? (
          <span className="form-field__error" id="login-error">
            {errors.login}
          </span>
        ) : null}
      </label>

      <label className="form-field">
        <span className="form-field__label">Пароль</span>
        <span className="auth-input">
          <span className="auth-input__icon" aria-hidden="true">
            <LockKeyhole size={18} strokeWidth={2} />
          </span>
          <input
            aria-describedby={errors.password ? "login-password-error" : undefined}
            aria-invalid={Boolean(errors.password)}
            autoComplete="current-password"
            disabled={loginMutation.isPending}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Введите пароль"
            type={showPassword ? "text" : "password"}
            value={password}
          />
          <button
            aria-label={showPassword ? "Скрыть пароль" : "Показать пароль"}
            className="auth-input__action"
            disabled={loginMutation.isPending}
            onClick={() => setShowPassword((value) => !value)}
            type="button"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </span>
        {errors.password ? (
          <span className="form-field__error" id="login-password-error">
            {errors.password}
          </span>
        ) : null}
      </label>

      <Checkbox className="auth-checkbox" isSelected={rememberMe} onChange={setRememberMe}>
        <span>Оставаться в системе</span>
      </Checkbox>

      {loginMutation.isError ? (
        <div className="auth-alert" role="alert">
          {getAuthErrorMessage(loginMutation.error)}
        </div>
      ) : null}

      <PrimaryButton disabled={loginMutation.isPending} type="submit">
        {loginMutation.isPending ? "Входим..." : "Войти"}
      </PrimaryButton>

      <Link className="secondary-button" to="/register">
        Создать аккаунт
      </Link>
    </form>
  );
}
