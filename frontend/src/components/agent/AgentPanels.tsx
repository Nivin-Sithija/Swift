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
import { useEffect, useState } from "react";
import type { InternalNote, Ticket, TicketPrediction } from "../../types";
import { ConfidenceIndicator, humanize } from "../tickets/TicketComponents";
import { ConfirmationDialog } from "../common/Controls";
import { ticketService } from "../../services/serviceSelector";
import { formatDate } from "../../lib/utils";

export function ImageEvidencePanel({ ticket }: { ticket: Ticket }) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let blobUrl = "";
    if (ticket.attachment) {
      if (ticketService.downloadAttachment) {
        ticketService
          .downloadAttachment(ticket.attachment.id)
          .then((url) => {
            if (active) {
              blobUrl = url;
              setImageUrl(url);
            }
          })
          .catch((err) => {
            console.error("Failed to load attachment image", err);
          });
      } else if (ticket.attachment.url) {
        setImageUrl(ticket.attachment.url);
      }
    }
    return () => {
      active = false;
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [ticket.attachment]);

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
          {imageUrl ? (
            <img
              className="evidence-image"
              src={imageUrl}
              alt="Uploaded evidence"
            />
          ) : (
            <div className="empty-inline"><LoaderCircle className="spin" /> Loading image...</div>
          )}
          {ticket.imageEvidence.status === "processed" ? (
            <div className="ocr-box">
              <div className="row spread">
                <strong>OCR-extracted text</strong>
                {ticket.imageEvidence.confidence !== undefined && (
                  <span>{ticket.imageEvidence.confidence}% confidence</span>
                )}
              </div>
              <pre>{ticket.imageEvidence.ocrText}</pre>
            </div>
          ) : (
            <div className="warning-box">
              <AlertTriangle />
              {ticket.imageEvidence.status === "processing"
                ? "OCR text is not available yet. Review the original image manually."
                : "OCR processing failed. Review the original image manually."}{" "}
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
  disabled = false,
}: {
  title: string;
  prediction: TicketPrediction;
  options: readonly string[];
  onSave: (value: string, reason: string) => Promise<boolean>;
  criticalReason?: string;
  disabled?: boolean;
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
        Change prediction
        <select
          disabled={disabled}
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
            disabled={disabled}
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
          disabled={disabled || saved}
          onClick={async () => {
            setValue(prediction.value);
            setSaved(
              await onSave(prediction.value, "Prediction accepted by agent."),
            );
          }}
        >
          <Check />
          {saved ? "Accepted" : "Accept"}
        </button>
        <button
          className="btn small"
          disabled={
            disabled || value === prediction.value || reason.trim().length < 3
          }
          onClick={async () => {
            setSaved(await onSave(value, reason));
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
  onSaveDraft,
  disabled = false,
}: {
  ticket: Ticket;
  onApproved: (text: string) => Promise<boolean>;
  onSaveDraft: (text: string, status: "draft" | "rejected") => Promise<boolean>;
  disabled?: boolean;
}) {
  const [text, setText] = useState(ticket.draft.text);
  const [saved, setSaved] = useState(ticket.draft.text);
  const [dialog, setDialog] = useState<"approve" | "reject" | null>(null);
  useEffect(() => {
    setText(ticket.draft.text);
    setSaved(ticket.draft.text);
  }, [ticket.draft.text]);
  const dirty = text !== saved;
  const approved = ticket.draft.status === "approved";
  const locked = disabled || approved;
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");
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
          <select disabled value={ticket.draft.language}>
            <option value="english">English</option>
            <option value="sinhala">සිංහල</option>
            <option value="tamil">தமிழ்</option>
          </select>
        </label>
        <button
          className="btn ghost small"
          disabled={locked}
          onClick={() =>
            setText(
              `Thank you for contacting Swift Support about ${ticket.subject}. We are reviewing the information you provided and will update you through this ticket.`,
            )
          }
        >
          <RefreshCw />
          Use response template
        </button>
        <button
          className="btn ghost small"
          disabled={!text.trim()}
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(text);
              setCopied(true);
              setCopyError("");
            } catch {
              setCopyError(
                "Could not copy. Select and copy the text manually.",
              );
            }
          }}
        >
          <Clipboard />
          {copied ? "Copied" : "Copy"}
        </button>
        <button
          className="btn ghost small"
          disabled={locked || !text}
          onClick={() => setText("")}
        >
          <Trash2 />
          Clear
        </button>
      </div>
      <label>
        <span className="sr-only">Response draft</span>
        <textarea
          disabled={locked}
          maxLength={5000}
          className="response-textarea"
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setCopied(false);
          }}
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
      {copyError && <small role="alert">{copyError}</small>}
      <div className="editor-actions">
        <button
          className="btn secondary"
          disabled={locked || !dirty || !text.trim()}
          onClick={async () => {
            if (await onSaveDraft(text, "draft")) setSaved(text);
          }}
        >
          <Save />
          {dirty ? "Save draft" : "Draft saved"}
        </button>
        <button
          disabled={locked || ticket.draft.status === "rejected"}
          className="btn danger-outline"
          onClick={() => setDialog("reject")}
        >
          {ticket.draft.status === "rejected"
            ? "Draft rejected"
            : "Reject draft"}
        </button>
        <button
          className="btn success"
          disabled={locked || !text.trim()}
          onClick={() => setDialog("approve")}
        >
          <Send />
          {approved ? "Response approved" : "Approve response"}
        </button>
      </div>
      <ConfirmationDialog
        busy={disabled}
        open={dialog === "approve"}
        title="Approve customer response?"
        description="This will mark the reviewed draft as the final customer-visible response."
        confirmLabel="Approve and send"
        onCancel={() => setDialog(null)}
        onConfirm={async () => {
          if (await onApproved(text)) {
            setSaved(text);
            setDialog(null);
          }
        }}
      />
      <ConfirmationDialog
        busy={disabled}
        open={dialog === "reject"}
        title="Reject AI draft?"
        description="The current generated draft will be cleared. This cannot be undone."
        confirmLabel="Reject draft"
        danger
        onCancel={() => setDialog(null)}
        onConfirm={async () => {
          if (await onSaveDraft(text, "rejected")) {
            setDialog(null);
          }
        }}
      />
    </section>
  );
}
