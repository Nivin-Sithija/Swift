import { Construction, Home, SearchX } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/layout/Layouts";
export function PlaceholderPage({ title }: { title: string }) {
  return (
    <>
      <PageHeader eyebrow="Planned feature" title={title} />
      <div className="empty card">
        <Construction />
        <h2>{title} is coming next</h2>
        <p>
          The navigation route is ready, while this academic frontend keeps its
          focus on complete ticket workflows.
        </p>
        <Link className="btn" to="/agent/dashboard">
          Return to dashboard
        </Link>
      </div>
    </>
  );
}
export function NotFoundPage() {
  return (
    <main className="not-found">
      <SearchX />
      <span className="eyebrow">Error 404</span>
      <h1>This page slipped out of the queue.</h1>
      <p>The address may be incorrect or the page may have moved.</p>
      <Link className="btn" to="/login">
        <Home />
        Return to Swift
      </Link>
    </main>
  );
}
