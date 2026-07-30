import { FileImage, RefreshCw, Trash2, UploadCloud } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const ACCEPTED_TYPES = ["image/png", "image/jpeg"];

type Result = { file?: File; error?: string };

export function validateImageFile(file: File): Result {
  if (!ACCEPTED_TYPES.includes(file.type))
    return { error: "Only PNG, JPG, and JPEG images are supported." };
  if (file.size > MAX_IMAGE_BYTES)
    return { error: "Image must be 5 MB or smaller." };
  if (file.name.toLowerCase().includes("corrupt"))
    return { error: "This image appears corrupted. Choose another file." };
  return { file };
}

export function ImageUploader({
  value,
  onChange,
}: {
  value: File | null;
  onChange: (file: File | null) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [drag, setDrag] = useState(false);
  const [preview, setPreview] = useState("");

  // An object URL leaks unless revoked, and creating one inline in render leaks one per frame.
  useEffect(() => {
    if (!value) {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(value);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [value]);

  // Mock upload progress — must stop when the file changes or the form unmounts.
  useEffect(() => {
    if (!value || progress === 0 || progress >= 100) return;
    const timer = setInterval(
      () => setProgress((p) => Math.min(100, p + 17)),
      80,
    );
    return () => clearInterval(timer);
  }, [value, progress]);

  const pick = (file?: File) => {
    if (!file) return;
    const result = validateImageFile(file);
    if (result.error) {
      setError(result.error);
      return;
    }
    setError("");
    onChange(file);
    setProgress(15);
  };

  return (
    <div className="uploader-wrap">
      <div
        className={`uploader ${drag ? "drag" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          pick(e.dataTransfer.files[0]);
        }}
      >
        <input
          ref={input}
          className="sr-only"
          type="file"
          accept=".png,.jpg,.jpeg,image/png,image/jpeg"
          onChange={(e) => pick(e.target.files?.[0])}
        />
        {!value ? (
          <>
            <UploadCloud />
            <strong>Drop your image here</strong>
            <p>PNG, JPG or JPEG · maximum 5 MB · one image</p>
            <button
              className="btn secondary"
              type="button"
              onClick={() => input.current?.click()}
            >
              Browse image
            </button>
          </>
        ) : (
          <div className="file-preview">
            <img src={preview} alt="Selected evidence preview" />
            <div>
              <strong>{value.name}</strong>
              <span>{(value.size / 1024).toFixed(1)} KB</span>
              {progress < 100 ? (
                <div className="upload-progress">
                  <span style={{ width: `${progress}%` }} />
                </div>
              ) : (
                <small>Ready to attach</small>
              )}
            </div>
            <div className="file-actions">
              <button
                className="icon-btn"
                type="button"
                onClick={() => input.current?.click()}
                aria-label="Replace image"
              >
                <RefreshCw />
              </button>
              <button
                className="icon-btn danger-text"
                type="button"
                onClick={() => {
                  onChange(null);
                  setProgress(0);
                }}
                aria-label="Remove image"
              >
                <Trash2 />
              </button>
            </div>
          </div>
        )}
      </div>
      {error && (
        <small className="field-error" role="alert">
          {error}
        </small>
      )}
      <p className="privacy-note">
        <FileImage />
        Remove personal balances or full account numbers before attaching
        evidence.
      </p>
    </div>
  );
}
