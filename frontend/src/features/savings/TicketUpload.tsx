// SPDX-License-Identifier: MIT
/**
 * Transit-ticket upload. Drag-and-drop or pick an image; the file is previewed
 * locally and never logged. On submit the backend runs vision extraction and
 * returns the verified saving plus the fields it read, which the parent shows
 * for confirmation. Client-side guards reject non-images and oversized files
 * before any upload.
 */

import {
  useEffect,
  useId,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
} from "react";

import { Emoji } from "../../shared/ui/Emoji";

interface TicketUploadProps {
  onSubmit: (file: File) => void;
  pending: boolean;
}

const MAX_BYTES = 8 * 1024 * 1024; // 8 MB

function validate(file: File): string | null {
  if (!file.type.startsWith("image/")) {
    return "Please choose an image of your ticket (PNG or JPEG).";
  }
  if (file.size > MAX_BYTES) {
    return "That image is too large. Keep it under 8 MB.";
  }
  return null;
}

export function TicketUpload({ onSubmit, pending }: TicketUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const errorId = useId();

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function accept(next: File) {
    const message = validate(next);
    if (message) {
      setError(message);
      return;
    }
    setError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(next);
    setPreviewUrl(URL.createObjectURL(next));
  }

  function handleInput(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.files?.[0];
    if (next) accept(next);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const next = event.dataTransfer.files?.[0];
    if (next) accept(next);
  }

  function handleSubmit() {
    if (file) onSubmit(file);
  }

  return (
    <div>
      <h2>
        <Emoji name="ticket" /> Upload a transit ticket
      </h2>
      <p className="form-hint">
        We read the route from the image to verify your trip. The image isn&apos;t
        stored or logged.
      </p>

      <div
        className={dragging ? "dropzone dropzone--active" : "dropzone"}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <label htmlFor={inputId} className="dropzone-label">
          <Emoji name="ticket" /> Drag a ticket image here, or choose a file
        </label>
        <input
          id={inputId}
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleInput}
          aria-describedby={error ? errorId : undefined}
        />
      </div>

      {error ? (
        <p id={errorId} role="alert" className="field-error">
          {error}
        </p>
      ) : null}

      {previewUrl ? (
        <div className="ticket-preview">
          <img src={previewUrl} alt="Selected ticket preview" />
          <p>{file?.name}</p>
          <button type="button" onClick={handleSubmit} disabled={pending}>
            {pending ? "Verifying…" : "Verify & log saving"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
