"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const MAX_SIZE_MB = 5;

export function CsvDropzone({ onFileSelected, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith(".csv")) {
        alert("Only .csv files are supported.");
        return;
      }
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        alert(`File exceeds the ${MAX_SIZE_MB}MB limit.`);
        return;
      }
      onFileSelected(file);
    },
    [onFileSelected],
  );

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border",
        disabled && "pointer-events-none opacity-50",
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        validateAndSelect(e.dataTransfer.files[0]);
      }}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
    >
      <UploadCloud className="h-10 w-10 text-muted-foreground" />
      <div>
        <p className="font-medium">Drag and drop your CSV file here</p>
        <p className="mt-1 text-sm text-muted-foreground">or click to browse (max {MAX_SIZE_MB}MB)</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => validateAndSelect(e.target.files?.[0])}
      />
    </div>
  );
}
