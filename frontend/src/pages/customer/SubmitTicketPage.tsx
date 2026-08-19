import { ArrowRight, RotateCcw, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { ticketService } from "../../services/serviceSelector";
import type { Ticket } from "../../types";
import { PageHeader } from "../../components/layout/Layouts";
import { ImageUploader } from "../../components/tickets/ImageUploader";
import {
  ProcessingStepper,
  PriorityBadge,
  StatusBadge,
} from "../../components/tickets/TicketComponents";
import { formatDate } from "../../lib/utils";
import { useLanguage } from "../../app/providers/LanguageProvider";
const schema = z.object({
  subject: z.string().min(5, "Use at least 5 characters").max(150),
  description: z
    .string()
    .min(15, "Please provide at least 15 characters")
    .max(5000),
  language: z.enum(["english", "sinhala", "tamil"]),
  terms: z.literal(true, { error: "You must acknowledge the privacy notice" }),
});
type Data = z.infer<typeof schema>;
const placeholders = [
  "My card payment was deducted, but the merchant says the transaction failed.",
  "මගේ කාඩ් ගෙවීම අසාර්ථක වුණත් මුදල අඩු වෙලා තියෙනවා.",
  "எனது அட்டை கட்டணம் தோல்வியடைந்தது, ஆனால் பணம் கழிக்கப்பட்டுள்ளது.",
  "mage card payment eka fail una, eth amount eka deduct wela.",
  "en card payment fail aayiduchu, aana amount deduct aayirukku.",
  "My transfer eka pending. කරුණාකර check කරන්න.",
];
const steps = [
  "Validating ticket",
  "Preserving original message",
  "Detecting language form",
  "Predicting category",
  "Predicting priority",
  "Analysing sentiment",
  "Processing image evidence",
  "Creating ticket",
];
const textOnlySteps = steps.filter((step) => step !== "Processing image evidence");
export function SubmitTicketPage() {
  const { tr } = useLanguage();
  const [file, setFile] = useState<File | null>(null);
  const [placeholder, setPlaceholder] = useState(0);
  const [processing, setProcessing] = useState(-1);
  const [confirmation, setConfirmation] = useState(false);
  const [createdTicket, setCreatedTicket] = useState<Ticket | null>(null);
  const [submitError, setSubmitError] = useState("");
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<Data>({
    resolver: zodResolver(schema),
    defaultValues: {
      subject: "",
      description: "",
      language: "english",
      terms: false as true,
    },
  });
  const subject = watch("subject");
  const description = watch("description");
  const processingActive = processing >= 0;
  const processingSteps = file ? steps : textOnlySteps;
  useEffect(() => {
    const id = setInterval(
      () => setPlaceholder((p) => (p + 1) % placeholders.length),
      4000,
    );
    return () => clearInterval(id);
  }, []);
  useEffect(() => {
    if (!processingActive) return;
    const id = window.setInterval(
      () =>
        setProcessing((current) =>
          Math.min(current + 1, processingSteps.length - 2),
        ),
      550,
    );
    return () => window.clearInterval(id);
  }, [processingActive, processingSteps.length]);
  const submit = async (data: Data) => {
    setSubmitError("");
    setProcessing(0);
    try {
      const created = ticketService.createTicket
        ? await ticketService.createTicket({
            subject: data.subject,
            message: data.description,
            preferredResponseLanguage: data.language,
            attachment: file,
          })
        : null;
      setCreatedTicket(created);
      setConfirmation(true);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Ticket submission failed");
    } finally {
      setProcessing(-1);
    }
  };
  if (confirmation)
    return (
      <div className="narrow-page confirmation">
        <div className="success-icon">
          <ShieldCheck />
        </div>
        <span className="eyebrow">Ticket created successfully</span>
        <h1>Your request is safely on its way.</h1>
        <p>
          We preserved your original message and prepared advisory
          classifications for the support team.
        </p>
        <div className="confirmation-card">
          <div>
            <span>Ticket ID</span>
            <strong>{createdTicket?.id || "SW-2026-1043"}</strong>
          </div>
          <div>
            <span>Submitted</span>
            <strong>{formatDate(new Date().toISOString())}</strong>
          </div>
          <div>
            <span>{tr("Language")}</span>
            <strong>{createdTicket?.language || "Pending analysis"}</strong>
          </div>
          <div>
            <span>{tr("Category")}</span>
            <strong>{createdTicket?.category.value || "Pending analysis"}</strong>
          </div>
          <div>
            <span>{tr("Priority")}</span>
            <PriorityBadge value={createdTicket?.priority.value || "medium"} />
          </div>
          <div>
            <span>{tr("Status")}</span>
            <StatusBadge value={createdTicket?.status || "new"} />
          </div>
          <div>
            <span>Image processing</span>
            <strong>{file ? "Evidence queued" : "No image attached"}</strong>
          </div>
        </div>
        <div className="confirmation-actions">
          <Link className="btn" to={`/customer/tickets/${createdTicket?.id || "SW-2026-1042"}`}>
            {tr("View ticket")} <ArrowRight />
          </Link>
          <button
            className="btn secondary"
            onClick={() => {
              setConfirmation(false);
              reset();
              setFile(null);
            }}
          >
            {tr("Submit another ticket")}
          </button>
        </div>
      </div>
    );
  return (
    <>
      <PageHeader
        eyebrow={tr("Customer support")}
        title={tr("How can we help?")}
        description="Write naturally in English, සිංහල, தமிழ், Singlish, Tanglish, or a mix. Your original wording is always preserved."
      />
      <div className="submit-grid">
        <form
          className="card form-card"
          onSubmit={handleSubmit(submit)}
          noValidate
        >
          <div className="section-heading">
            <span>1</span>
            <div>
              <h2>{tr("Tell us what happened")}</h2>
              <p>Do not include passwords, PINs or full card numbers.</p>
            </div>
          </div>
          <label>
            {tr("Subject")} <span className="required">*</span>
            <input
              {...register("subject")}
              placeholder="A short summary of the issue"
              maxLength={150}
            />
            <span className="field-meta">
              {errors.subject ? (
                <small className="field-error">{errors.subject.message}</small>
              ) : (
                <small>Be specific so we can route it correctly.</small>
              )}
              <small>{subject.length}/150</small>
            </span>
          </label>
          <label>
            {tr("Detailed description")} <span className="required">*</span>
            <textarea
              {...register("description")}
              placeholder={placeholders[placeholder]}
              rows={8}
              maxLength={5000}
            />
            <span className="field-meta">
              {errors.description ? (
                <small className="field-error">
                  {errors.description.message}
                </small>
              ) : (
                <small>
                  Line breaks and original Unicode text are preserved.
                </small>
              )}
              <small>{description.length}/5,000</small>
            </span>
          </label>
          <label>
            {tr("Preferred response language")}
            <select {...register("language")}>
              <option value="english">English</option>
              <option value="sinhala">සිංහල</option>
              <option value="tamil">தமிழ்</option>
            </select>
          </label>
          <label>
            {tr("Category selection")}
            <input value={tr("Let the system detect")} disabled />
            <small>Agents can review and correct advisory predictions.</small>
          </label>
          <div className="section-heading">
            <span>2</span>
            <div>
              <h2>
                {tr("Add image evidence")} <em>{tr("Optional")}</em>
              </h2>
              <p>
                A screenshot, receipt, transaction slip or error screen can
                help.
              </p>
            </div>
          </div>
          <ImageUploader value={file} onChange={setFile} />
          <label className="checkbox terms">
            <input type="checkbox" {...register("terms")} />
            <span>
              I acknowledge the privacy notice and confirm this ticket contains
              no passwords, PINs, or complete payment-card details.
            </span>
          </label>
          {errors.terms && (
            <small className="field-error">{errors.terms.message}</small>
          )}
          {submitError && <small className="field-error">{submitError}</small>}
          <div className="form-actions">
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                reset();
                setFile(null);
              }}
            >
              <RotateCcw />
              {tr("Clear")}
            </button>
            <button className="btn" disabled={processingActive}>
              {processingActive ? "Submitting…" : tr("Submit ticket")} <ArrowRight />
            </button>
          </div>
        </form>
        <aside className="support-aside">
          <div className="card">
            <h3>{tr("Before you submit")}</h3>
            <ul className="check-list">
              <li>Describe what you expected to happen.</li>
              <li>Include an approximate date or reference if safe.</li>
              <li>Attach only relevant, redacted evidence.</li>
            </ul>
          </div>
          <div className="card subtle">
            <ShieldCheck />
            <h3>{tr("Human review is built in")}</h3>
            <p>
              Automated analysis helps route your request. An authorised support
              agent reviews responses before approval.
            </p>
          </div>
        </aside>
      </div>
      {processing >= 0 && (
        <div className="processing-overlay">
          <div className="processing-modal" role="status" aria-live="polite">
            <span className="eyebrow">Creating secure ticket</span>
            <h2>Analysing your request</h2>
            <p>
              Please keep this window open. No real banking systems are
              contacted.
            </p>
            <ProcessingStepper current={processing} steps={processingSteps} />
          </div>
        </div>
      )}
    </>
  );
}
