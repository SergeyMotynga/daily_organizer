import { FormEvent, useState } from "react";
import { Eye, EyeOff, LockKeyhole, UserRound } from "lucide-react";
import { Link } from "react-router";

import type { User } from "../entities/user/types";
import { PrimaryButton } from "../features/auth/primary-button";
import { getAuthErrorMessage, useRegisterMutation } from "../features/auth/session";

type RegisterFormErrors = {
  name?: string;
  login?: string;
  password?: string;
  passwordRepeat?: string;
};

function getPasswordError(password: string): string | undefined {
  if (password.length < 8 || password.length > 30) {
    return "Пароль должен быть от 8 до 30 символов.";
  }

  if (/\s/.test(password)) {
    return "Пароль не должен содержать пробелы.";
  }

  if (!/^[A-Za-z0-9]+$/.test(password)) {
    return "Используйте только латинские буквы и цифры.";
  }

  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return "Пароль должен содержать латинскую букву и цифру.";
  }

  return undefined;
}

function validateRegisterForm(
  name: string,
  login: string,
  password: string,
  passwordRepeat: string
): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  if (!name.trim()) {
    errors.name = "Введите имя.";
  }

  if (!login.trim()) {
    errors.login = "Введите login.";
  }

  if (!password) {
    errors.password = "Введите пароль.";
  } else {
    errors.password = getPasswordError(password);
  }

  if (!passwordRepeat) {
    errors.passwordRepeat = "Повторите пароль.";
  } else if (password && passwordRepeat !== password) {
    errors.passwordRepeat = "Пароли не совпадают.";
  }

  return Object.fromEntries(Object.entries(errors).filter(([, value]) => Boolean(value)));
}

export function RegisterPage() {
  const registerMutation = useRegisterMutation();
  const [createdUser, setCreatedUser] = useState<User | null>(null);
  const [name, setName] = useState("");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [passwordRepeat, setPasswordRepeat] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordRepeat, setShowPasswordRepeat] = useState(false);
  const [errors, setErrors] = useState<RegisterFormErrors>({});

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validateRegisterForm(name, login, password, passwordRepeat);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    try {
      const user = await registerMutation.mutateAsync({
        name: name.trim(),
        login: login.trim(),
        password
      });
      setCreatedUser(user);
    } catch {
      return;
    }
  }

  if (createdUser) {
    return (
      <div className="auth-success" role="status">
        <h1 id="register-title">Аккаунт создан</h1>
        <p>{createdUser.name}, регистрация завершена. Теперь войдите в аккаунт, чтобы начать работу.</p>
        <span className="primary-button-shell">
          <span className="primary-button-shell__glow" aria-hidden="true" />
          <Link className="primary-button" to="/login">
            Перейти ко входу
          </Link>
        </span>
      </div>
    );
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <h1 id="register-title">Создать аккаунт</h1>

      <div className="auth-form__grid">
        <label className="form-field">
          <span className="form-field__label">Имя</span>
          <span className="auth-input">
            <span className="auth-input__icon" aria-hidden="true">
              <UserRound size={18} strokeWidth={2} />
            </span>
            <input
              aria-describedby={errors.name ? "register-name-error" : undefined}
              aria-invalid={Boolean(errors.name)}
              autoComplete="name"
              disabled={registerMutation.isPending}
              onChange={(event) => setName(event.target.value)}
              placeholder="Введите имя"
              value={name}
            />
          </span>
          {errors.name ? (
            <span className="form-field__error" id="register-name-error">
              {errors.name}
            </span>
          ) : null}
        </label>

        <label className="form-field">
          <span className="form-field__label">Логин</span>
          <span className="auth-input">
            <span className="auth-input__icon" aria-hidden="true">
              <UserRound size={18} strokeWidth={2} />
            </span>
            <input
              aria-describedby={errors.login ? "register-login-error" : undefined}
              aria-invalid={Boolean(errors.login)}
              autoComplete="username"
              disabled={registerMutation.isPending}
              onChange={(event) => setLogin(event.target.value)}
              placeholder="Введите логин"
              value={login}
            />
          </span>
          {errors.login ? (
            <span className="form-field__error" id="register-login-error">
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
              aria-describedby={errors.password ? "register-password-error" : undefined}
              aria-invalid={Boolean(errors.password)}
              autoComplete="new-password"
              disabled={registerMutation.isPending}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Введите пароль"
              type={showPassword ? "text" : "password"}
              value={password}
            />
            <button
              aria-label={showPassword ? "Скрыть пароль" : "Показать пароль"}
              className="auth-input__action"
              disabled={registerMutation.isPending}
              onClick={() => setShowPassword((value) => !value)}
              type="button"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </span>
          {errors.password ? (
            <span className="form-field__error" id="register-password-error">
              {errors.password}
            </span>
          ) : null}
        </label>

        <label className="form-field">
          <span className="form-field__label">Повторите пароль</span>
          <span className="auth-input">
            <span className="auth-input__icon" aria-hidden="true">
              <LockKeyhole size={18} strokeWidth={2} />
            </span>
            <input
              aria-describedby={
                errors.passwordRepeat ? "register-password-repeat-error" : undefined
              }
              aria-invalid={Boolean(errors.passwordRepeat)}
              autoComplete="new-password"
              disabled={registerMutation.isPending}
              onChange={(event) => setPasswordRepeat(event.target.value)}
              placeholder="Повторите пароль"
              type={showPasswordRepeat ? "text" : "password"}
              value={passwordRepeat}
            />
            <button
              aria-label={showPasswordRepeat ? "Скрыть пароль" : "Показать пароль"}
              className="auth-input__action"
              disabled={registerMutation.isPending}
              onClick={() => setShowPasswordRepeat((value) => !value)}
              type="button"
            >
              {showPasswordRepeat ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </span>
          {errors.passwordRepeat ? (
            <span className="form-field__error" id="register-password-repeat-error">
              {errors.passwordRepeat}
            </span>
          ) : null}
        </label>
      </div>

      {registerMutation.isError ? (
        <div className="auth-alert" role="alert">
          {getAuthErrorMessage(registerMutation.error)}
        </div>
      ) : null}

      <PrimaryButton disabled={registerMutation.isPending} type="submit">
        {registerMutation.isPending ? "Создаем..." : "Создать аккаунт"}
      </PrimaryButton>

      <p className="auth-switch">
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </p>
    </form>
  );
}
