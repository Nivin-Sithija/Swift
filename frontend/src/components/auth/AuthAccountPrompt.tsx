import { Link } from "react-router-dom";
import type { UserRole } from "../../types";

export function AuthAccountPrompt({
  view,
  role,
}: {
  view: "login" | "register";
  role: UserRole;
}) {
  if (view === "login") {
    if (role === "administrator") return null;
    return (
      <p className="demo-hint">
        New to Swift?{" "}
        <Link className="link-button" to={`/register?role=${role}`}>
          Create an account
        </Link>
      </p>
    );
  }

  return (
    <p className="demo-hint">
      Already registered?{" "}
      <Link
        className="link-button"
        to={role === "agent" ? "/admin/login" : "/login"}
      >
        Sign in
      </Link>
    </p>
  );
}
