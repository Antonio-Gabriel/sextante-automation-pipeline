import { useState } from "react";

/** The files picked or dropped, without repeats of the same name and size. */
export function useFileSelection() {
  const [files, setFiles] = useState<File[]>([]);
  const add = (incoming: Iterable<File>) =>
    setFiles((current) => {
      const known = new Set(current.map(fileKey));
      return [...current, ...[...incoming].filter((file) => !known.has(fileKey(file)))];
    });
  const remove = (file: File) => setFiles((current) => current.filter((f) => f !== file));
  const clear = () => setFiles([]);
  return { files, add, remove, clear };
}

function fileKey(file: File): string {
  return `${file.name}:${file.size}`;
}
