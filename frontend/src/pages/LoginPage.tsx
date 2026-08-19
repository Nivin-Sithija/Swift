import { Eye, EyeOff, LoaderCircle, LockKeyhole, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "../app/providers/AuthProvider";
import {
  LanguageSelector,
  Logo,
  ThemeSwitcher,
} from "../components/common/Controls";
import type { UserRole } from "../types";
import { useLanguage } from "../app/providers/LanguageProvider";
import { isMockMode } from "../lib/config";

const schema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(8, "Password must contain at least 8 characters"),
  remember: z.boolean(),
});
type FormData = z.infer<typeof schema>;
export function LoginPage() {
  const { tr } = useLanguage();
  const mockMode = isMockMode();
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<UserRole>("customer");
  const [show, setShow] = useState(false);
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", remember: false },
  });
  if (user)
    return (
      <Navigate
        to={user.role === "administrator" ? "/admin/dashboard" : user.role === "agent" ? "/agent/dashboard" : "/customer/submit"}
        replace
      />
    );
  const useDemo = () => {
    setValue(
      "email",
      role === "administrator"
        ? "admin@swift.demo"
        : role === "agent"
          ? "agent@swift.demo"
          : "customer@swift.demo",
    );
    setValue("password", "password123");
  };
  return (
    <main className="login-page">
      <div className="login-brand">
        <Logo />
        <div className="brand-copy">
          <span className="eyebrow">Secure support, thoughtfully routed</span>
          <h1>Financial support that understands every voice.</h1>
          <p>
            Submit banking support requests in English, සිංහල, தமிழ், or natural
            mixed language. Every AI-assisted response remains under human
            review.
          </p>
        </div>
        <div className="trust-list">
          <span>
            <ShieldCheck />
            Human-approved responses
          </span>
          <span>
            <LockKeyhole />
            Mock prototype · no real banking access
          </span>
        </div>
      </div>
      <section className="login-panel">
        <div className="login-tools">
          <LanguageSelector />
          <ThemeSwitcher />
        </div>
        <div className="login-form-wrap">
          <span className="mobile-logo">
            <Logo />
          </span>
          <h2>{tr("Welcome to Swift")}</h2>
          <p>Sign in to continue to your secure support workspace.</p>
          <div
            className="role-tabs"
            role="tablist"
            aria-label="Select account type"
          >
            <button
              role="tab"
              aria-selected={role === "customer"}
              onClick={() => {
                setRole("customer");
                setServerError("");
              }}
            >
              {tr("Customer")}
            </button>
            <button
              role="tab"
              aria-selected={role === "agent"}
              onClick={() => {
                setRole("agent");
                setServerError("");
              }}
            >
              {tr("Support agent")}
            </button>
            {mockMode && (
              <button
                role="tab"
                aria-selected={role === "administrator"}
                onClick={() => {
                  setRole("administrator");
                  setServerError("");
                }}
              >
                Administrator
              </button>
            )}
          </div>
          <form
            onSubmit={handleSubmit(async (data) => {
              try {
                setServerError("");
                const signedIn = await login(data.email, data.password, role, data.remember);
                navigate(
                  signedIn.role === "administrator"
                    ? "/admin/dashboard"
                    : signedIn.role === "agent"
                      ? "/agent/dashboard"
                      : "/customer/submit",
                );
              } catch (error) {
                setServerError(
                  error instanceof Error ? error.message : "Unable to sign in",
                );
              }
            })}
            noValidate
          >
            <label>
              {tr("Email address")}
              <input
                autoComplete="email"
                {...register("email")}
                placeholder={
                  mockMode
                    ? role === "administrator"
                      ? "admin@swift.demo"
                      : role === "agent"
                        ? "agent@swift.demo"
                        : "customer@swift.demo"
                    : "you@example.com"
                }
              />
              {errors.email && (
                <small className="field-error">{errors.email.message}</small>
              )}
            </label>
            <label>
              {tr("Password")}
              <div className="password">
                <input
                  type={show ? "text" : "password"}
                  autoComplete="current-password"
                  {...register("password")}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShow(!show)}
                  aria-label={show ? "Hide password" : "Show password"}
                >
                  {show ? <EyeOff /> : <Eye />}
                </button>
              </div>
              {errors.password && (
                <small className="field-error">{errors.password.message}</small>
              )}
            </label>
            <div className="row spread">
              <label className="checkbox">
                <input type="checkbox" {...register("remember")} />
                {tr("Remember me")}
              </label>
              <button type="button" className="link-button">
                {tr("Forgot password?")}
              </button>
            </div>
            {serverError && (
              <div className="form-error" role="alert">
                {serverError}{mockMode ? ". Try the demo account below." : "."}
              </div>
            )}
            <button className="btn wide" disabled={isSubmitting}>
              {isSubmitting && <LoaderCircle className="spin" aria-hidden="true" />}
              {isSubmitting ? tr("Signing in…") : tr("Sign in securely")}
            </button>
            {mockMode && (
              <button
                type="button"
                className="btn secondary wide"
                disabled={isSubmitting}
                onClick={useDemo}
              >
                Use {role} demo account
              </button>
            )}
          </form>
          {mockMode && (
            <p className="demo-hint">
              Mock mode · Demo password: <code>password123</code>
            </p>
          )}
          <p className="demo-hint">
            New to Swift? <Link className="link-button" to={`/register?role=${role}`}>Create an account</Link>
          </p>
        </div>
      </section>
    </main>
  );
}
