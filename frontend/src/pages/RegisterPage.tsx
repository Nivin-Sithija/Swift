import { LockKeyhole, ShieldCheck, UserPlus } from "lucide-react";
import { Navigate, Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { useAuth } from "../app/providers/AuthProvider";
import { useLanguage } from "../app/providers/LanguageProvider";
import { LanguageSelector, Logo, ThemeSwitcher } from "../components/common/Controls";
import type { UserRole } from "../types";

const schema = z.object({
  name: z.string().trim().min(2, "Enter your full name").max(150),
  email: z.email("Enter a valid email address"),
  password: z.string().min(8, "Use at least 8 characters").max(128),
  confirmPassword: z.string(),
  agentCode: z.string().max(256).optional(),
}).refine((value) => value.password === value.confirmPassword, {
  path: ["confirmPassword"], message: "Passwords do not match",
});
type FormData = z.infer<typeof schema>;

export function RegisterPage() {
  const { user, register: createAccount } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();
  const [role, setRole] = useState<UserRole>("customer");
  const [serverError, setServerError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", password: "", confirmPassword: "", agentCode: "" },
  });
  if (user) return <Navigate to={user.role === "agent" ? "/agent/dashboard" : "/customer/submit"} replace />;
  const preferredLanguage = language === "si" ? "sinhala" : language === "ta" ? "tamil" : "english";
  return (
    <main className="login-page">
      <div className="login-brand">
        <Logo />
        <div className="brand-copy">
          <span className="eyebrow">Create your Swift workspace</span>
          <h1>Secure multilingual support starts here.</h1>
          <p>Customers can create an account immediately. Support-agent accounts require an organisation registration code.</p>
        </div>
        <div className="trust-list">
          <span><ShieldCheck /> Customer data stays role-protected</span>
          <span><LockKeyhole /> Staff access requires verification</span>
        </div>
      </div>
      <section className="login-panel">
        <div className="login-tools"><LanguageSelector /><ThemeSwitcher /></div>
        <div className="login-form-wrap">
          <span className="mobile-logo"><Logo /></span>
          <h2>Create an account</h2>
          <p>Choose the account type and enter your details.</p>
          <div className="role-tabs" role="tablist" aria-label="Select account type">
            <button type="button" role="tab" aria-selected={role === "customer"} onClick={() => { setRole("customer"); setServerError(""); }}>Customer</button>
            <button type="button" role="tab" aria-selected={role === "agent"} onClick={() => { setRole("agent"); setServerError(""); }}>Support agent</button>
          </div>
          <form onSubmit={handleSubmit(async (data) => {
            try {
              setServerError("");
              await createAccount({ name: data.name, email: data.email, password: data.password, role, preferredLanguage, agentCode: data.agentCode });
              navigate(role === "agent" ? "/agent/dashboard" : "/customer/submit");
            } catch (error) { setServerError(error instanceof Error ? error.message : "Unable to create account"); }
          })} noValidate>
            <label>Full name<input autoComplete="name" {...register("name")} placeholder="Your full name" />{errors.name && <small className="field-error">{errors.name.message}</small>}</label>
            <label>Email address<input autoComplete="email" {...register("email")} placeholder="you@example.com" />{errors.email && <small className="field-error">{errors.email.message}</small>}</label>
            <label>Password<input type="password" autoComplete="new-password" {...register("password")} placeholder="At least 8 characters" />{errors.password && <small className="field-error">{errors.password.message}</small>}</label>
            <label>Confirm password<input type="password" autoComplete="new-password" {...register("confirmPassword")} placeholder="Enter the password again" />{errors.confirmPassword && <small className="field-error">{errors.confirmPassword.message}</small>}</label>
            {role === "agent" && <label>Support-agent registration code<input type="password" autoComplete="off" {...register("agentCode")} placeholder="Provided by your organisation" /><small>Required to prevent unauthorised staff accounts.</small></label>}
            {serverError && <div className="form-error" role="alert">{serverError}</div>}
            <button className="btn wide" disabled={isSubmitting}><UserPlus />{isSubmitting ? "Creating account…" : "Create account"}</button>
          </form>
          <p className="demo-hint">Already registered? <Link className="link-button" to="/login">Sign in</Link></p>
        </div>
      </section>
    </main>
  );
}
