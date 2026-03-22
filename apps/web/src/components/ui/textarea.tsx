import * as React from "react";

import { cn } from "@/lib/utils";


export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea(
  { className, ...props },
  ref,
) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "min-h-28 w-full rounded-3xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-coral",
        className,
      )}
      {...props}
    />
  );
});
