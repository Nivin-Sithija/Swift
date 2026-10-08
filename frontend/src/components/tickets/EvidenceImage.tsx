import { AlertTriangle, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { ticketService } from "../../services/serviceSelector";
import type { Attachment } from "../../types";

type State =
  | { status: "loading" }
  | { status: "ready"; src: string }
  | { status: "failed" };

/** Uploaded ticket image, loaded through the authenticated API as a blob. */
export function EvidenceImage({
  attachment,
  alt,
}: {
  attachment: Attachment;
  alt: string;
}) {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let objectUrl: string | undefined;
    let cancelled = false;
    setState({ status: "loading" });
    ticketService
      .getAttachmentBlob(attachment.id)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setState({ status: "ready", src: objectUrl });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "failed" });
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attachment.id]);

  if (state.status === "loading")
    return (
      <div className="empty-inline" role="status">
        <LoaderCircle className="spin" /> Loading image…
      </div>
    );
  if (state.status === "failed")
    return (
      <div className="warning-box">
        <AlertTriangle />
        The uploaded image could not be loaded.
      </div>
    );
  return <img className="evidence-image" src={state.src} alt={alt} />;
}
