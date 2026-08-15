import {
  AlertTriangle,
  Check,
  Clipboard,
  FileImage,
  LoaderCircle,
  RefreshCw,
  Save,
  Send,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import type { InternalNote, Ticket, TicketPrediction } from "../../types";
import { ConfidenceIndicator, humanize } from "../tickets/TicketComponents";
import { ConfirmationDialog } from "../common/Controls";
import { formatDate } from "../../lib/utils";

export function ImageEvidencePanel({ ticket }: { ticket: Ticket }) {
  return (
    <section className="card">
      <div className="section-title">
        <FileImage />
        <div>
          <span className="eyebrow">Supplementary input</span>
          <h2>Image evidence</h2>
        </div>
        <span className={`badge status ${ticket.imageEvidence.status}`}>
          {humanize(ticket.imageEvidence.status)}
        </span>
      </div>
      {ticket.attachment ? (
        <>
          <img
            className="evidence-image"
            src={ticket.attachment.url}
            alt="Uploaded evidence"
          />
          {ticket.imageEvidence.status === "processed" ? (
            <div className="ocr-box">
              <div className="row spread">
                <strong>OCR-extracted text</strong>
                <span>{ticket.imageEvidence.confidence}% confidence</span>
              </div>
              <pre>{ticket.imageEvidence.ocrText}</pre>
            </div>
          ) : (
            <div className="warning-box">
              <AlertTriangle />
              OCR processing failed. Review the original image manually.{" "}
              <button className="btn small secondary">
                <RefreshCw />
                Retry
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="empty-inline">
          No image was attached to this ticket.
        </div>
      )}
      <p className="evidence-notice">
        <AlertTriangle />
        Image evidence is supplementary and must not override the customer's
        original message or agent judgement.
      </p>
    </section>
  );
}
export function PredictionCard({
  title,
  prediction,
  options,
  onSave,
  criticalReason,
}: {
  title: string;
  prediction: TicketPrediction;
  options: readonly string[];
  onSave: (value: string, reason: string) => void;
  criticalReason?: string;
}) {
  const [value, setValue] = useState(prediction.value);
  const [reason, setReason] = useState("");
  const [saved, setSaved] = useState(false);
  return (
    <section className="prediction-card">
      <div className="row spread">
        <span className="eyebrow">{title} prediction</span>
        <span className="ai-label">
          <Sparkles />
          AI advisory
        </span>
      </div>
      <div className="prediction-value">{humanize(prediction.value)}</div>
      <ConfidenceIndicator value={prediction.confidence} />
      {criticalReason && (
        <div className="critical-notice">
          <AlertTriangle />
          <span>
            <strong>Deterministic escalation rule</strong>
            {criticalReason}
          </span>
        </div>
      )}
      <div className="prediction-meta">
        <span>Model</span>
        <code>{prediction.modelVersion}</code>
        <span>Predicted</span>
        <small>{formatDate(prediction.predictedAt)}</small>
      </div>
      <label>
        Correct prediction
        <select
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setSaved(false);
          }}
        >
          {options.map((o) => (
            <option key={o} value={o}>
              {humanize(o)}
            </option>
          ))}
        </select>
      </label>
      {value !== prediction.value && (
        <label>
          Correction reason
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={2}
            placeholder="Required audit reason"
          />
        </label>
      )}
      <div className="row">
        <button
          className="btn small secondary"
          onClick={() => {
            setValue(prediction.value);
            setSaved(true);
          }}
        >
          <Check />
          Accept
        </button>
        <button
          className="btn small"
          disabled={value === prediction.value || !reason.trim()}
          onClick={() => {
            onSave(value, reason);
            setSaved(true);
          }}
        >
          <Save />
          Save correction
        </button>
        {saved && <small className="saved">Saved</small>}
      </div>
    </section>
  );
}
export function InternalNotes({
  initial,
  onAdd,
}: {
  initial: InternalNote[];
  onAdd: (text: string) => Promise<InternalNote>;
}) {
  const [notes, setNotes] = useState(initial);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <span className="eyebrow">Agent only</span>
          <h2>Internal notes</h2>
        </div>
        <span className="badge language">Not customer-visible</span>
      </div>
      <div className="notes">
        {notes.map((note) => (
          <article key={note.id}>
            <div className="row spread">
              <strong>{note.author}</strong>
              <time>{formatDate(note.at)}</time>
            </div>
            <p>{note.text}</p>
          </article>
        ))}
      </div>
      <label>
        Add note
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder="Add useful context for another agent…"
        />
      </label>
      {error && (
        <small className="field-error" role="alert">
          {error}
        </small>
      )}
      <div className="row end">
        <button
          className="btn secondary"
          disabled={!text.trim() || adding}
          onClick={async () => {
            try {
              setError("");
              setAdding(true);
              // The service owns note identity; render exactly what it stored.
              const note = await onAdd(text);
              setNotes((v) => [...v, note]);
              setText("");
            } catch (cause) {
              console.error("[InternalNotes/add]", cause);
              setError("The note could not be saved. Try again.");
            } finally {
              setAdding(false);
            }
          }}
        >
          {adding && <LoaderCircle className="spin" aria-hidden="true" />}
          {adding ? "Adding note…" : "Add internal note"}
        </button>
      </div>
    </section>
  );
}
export function ResponseEditor({
  ticket,
  onApproved,
}: {
  ticket: Ticket;
  onApproved: (text: string) => void;
}) {
  const [text, setText] = useState(ticket.draft.text);
  const [saved, setSaved] = useState(ticket.draft.text);
  const [dialog, setDialog] = useState<"approve" | "reject" | null>(null);
  const dirty = text !== saved;
  return (
    <section className="card response-editor">
      <div className="warning-box prominent">
        <AlertTriangle />
        <span>
          <strong>AI-generated draft.</strong> Verify all information before
          approval.
        </span>
      </div>
      <div className="card-heading">
        <div>
          <span className="eyebrow">Human review required</span>
          <h2>Response editor</h2>
        </div>
        <span className="ai-label">
          <Sparkles />
          AI-generated draft
        </span>
      </div>
      <div className="editor-toolbar">
        <label>
          Output language
          <select>
            <option>English</option>
            <option>සිංහල</option>
            <option>தமிழ்</option>
          </select>
        </label>
        <button
          className="btn ghost small"
          onClick={() =>
            setText(
              `Thank you for contacting Swift Support about ${ticket.subject}. We are reviewing the information you provided and will update you through this ticket.`,
            )
          }
        >
          <RefreshCw />
          Regenerate
        </button>
        <button
          className="btn ghost small"
          onClick={() => navigator.clipboard?.writeText(text)}
        >
          <Clipboard />
          Copy
        </button>
        <button className="btn ghost small" onClick={() => setText("")}>
          <Trash2 />
          Clear
        </button>
      </div>
      <label>
        <span className="sr-only">Response draft</span>
        <textarea
          className="response-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
        />
      </label>
      <div className="row spread">
        <small className={dirty ? "warning-text" : ""}>
          {dirty
            ? "Unsaved changes"
            : `${text.length} characters · Draft saved`}
        </small>
        <small>{text.length}/5,000</small>
      </div>
      <div className="editor-actions">
        <button
          className="btn secondary"
          disabled={!dirty}
          onClick={() => setSaved(text)}
        >
          <Save />
          Save draft
        </button>
        <button
          className="btn danger-outline"
          onClick={() => setDialog("reject")}
        >
          Reject draft
        </button>
        <button
          className="btn success"
          disabled={!text.trim()}
          onClick={() => setDialog("approve")}
        >
          <Send />
          Approve response
        </button>
      </div>
      <ConfirmationDialog
        open={dialog === "approve"}
        title="Approve customer response?"
        description="This will mark the reviewed draft as the final customer-visible response."
        confirmLabel="Approve and send"
        onCancel={() => setDialog(null)}
        onConfirm={() => {
          setSaved(text);
          setDialog(null);
          onApproved(text);
        }}
      />
      <ConfirmationDialog
        open={dialog === "reject"}
        title="Reject AI draft?"
        description="The current generated draft will be cleared. This cannot be undone in the mock session."
        confirmLabel="Reject draft"
        danger
        onCancel={() => setDialog(null)}
        onConfirm={() => {
          setText("");
          setDialog(null);
        }}
      />
    </section>
  );
}
