"use client";

import { useRef, useState } from "react";

export default function UploadZone({ onFile }: { onFile: (file: File) => void }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files?.[0];
        if (file) onFile(file);
      }}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-lg border-2 border-dashed px-6 py-14 text-center transition-colors ${
        dragActive ? "border-amber-signal bg-blueprint-900/60" : "border-blueprint-line/50 hover:border-amber-signal/60"
      }`}
    >
      <p className="font-mono text-xs tracking-widest text-amber-signal mb-2">DROP FILE</p>
      <p className="text-paper/70">Drag a P&amp;ID, work order, SOP, or inspection report here, or click to browse.</p>
      <p className="font-mono text-[11px] text-paper/40 mt-2">PDF, PNG, JPG — scanned documents run through OCR automatically</p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
        }}
      />
    </div>
  );
}
