"use client";

import { Input } from "@/components/ui/input";


export function FilterBar({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return <Input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />;
}
