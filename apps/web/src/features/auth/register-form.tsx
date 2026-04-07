"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { FieldErrors, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { apiFetch, saveAuthTokens } from "@/lib/api";

const schema = z.object({
  email: z.string().email("Please enter a valid email address."),
  verification_code: z.string().regex(/^\d{6}$/, "Please enter the 6-digit verification code."),
  full_name: z.string().min(2, "Full name must be at least 2 characters."),
  nickname: z.string().min(2, "Nickname must be at least 2 characters."),
  password: z.string().min(8, "Password must be at least 8 characters."),
});

type FormValues = z.infer<typeof schema>;

type LoginResponse = {
  access: string;
  refresh: string;
};

export function RegisterForm() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [sendCodeMessage, setSendCodeMessage] = useState<string | null>(null);
  const {
    clearErrors,
    getValues,
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const sendVerificationCode = async () => {
    const email = getValues("email");
    console.debug("[register] sendVerificationCode click", { email });

    const emailValidation = schema.shape.email.safeParse(email);
    if (!emailValidation.success) {
      console.warn("[register] sendVerificationCode blocked by email validation", {
        issues: emailValidation.error.issues,
      });
      setError("email", {
        message: emailValidation.error.issues[0]?.message ?? "Please enter a valid email address.",
      });
      return;
    }

    clearErrors("email");
    clearErrors("root");
    setSendCodeMessage(null);
    setIsSendingCode(true);

    try {
      await apiFetch("auth/email-code/request/", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email }),
      });
      setSendCodeMessage("Verification code sent. Please check your inbox.");
    } catch (error) {
      console.error("[register] sendVerificationCode failed", {
        error,
        stack: error instanceof Error ? error.stack : undefined,
      });
      setError("root", {
        message: error instanceof Error ? error.message : "Failed to send verification code.",
      });
    } finally {
      setIsSendingCode(false);
    }
  };

  const onValidSubmit = async (values: FormValues) => {
    console.debug("[register] submit valid", {
      email: values.email,
      payloadKeys: Object.keys(values),
    });

    try {
      await apiFetch("auth/register/", {
        method: "POST",
        auth: false,
        body: JSON.stringify(values),
      });

      const loginResponse = await apiFetch<LoginResponse>("auth/login/", {
        method: "POST",
        auth: false,
        body: JSON.stringify({
          email: values.email,
          password: values.password,
        }),
      });

      saveAuthTokens(loginResponse.access, loginResponse.refresh);
      startTransition(() => {
        router.push("/profile");
      });
    } catch (error) {
      console.error("[register] submit failed", {
        error,
        stack: error instanceof Error ? error.stack : undefined,
      });
      setError("root", {
        message: error instanceof Error ? error.message : "Registration failed.",
      });
    }
  };

  const onInvalidSubmit = (formErrors: FieldErrors<FormValues>) => {
    console.warn("[register] submit blocked by validation", formErrors);
  };

  const onSubmit = handleSubmit(onValidSubmit, onInvalidSubmit);

  return (
    <Card className="mx-auto w-full max-w-2xl bg-shell/95">
      <div className="space-y-6">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">Onboarding</p>
          <h1 className="font-serif text-3xl text-ink">Create your account</h1>
          <p className="text-sm text-slate-500">
            Request a verification code first, then finish registration. After success, you will be signed in
            automatically and redirected to your profile.
          </p>
        </div>

        <form className="grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
          <FormField label="Email" error={errors.email?.message}>
            <Input type="email" placeholder="name@university.edu.cn" {...register("email")} />
          </FormField>

          <div className="flex items-end gap-3">
            <div className="flex-1">
              <FormField label="Verification code" error={errors.verification_code?.message}>
                <Input
                  placeholder="6-digit code"
                  inputMode="numeric"
                  maxLength={6}
                  {...register("verification_code")}
                />
              </FormField>
            </div>
            <Button type="button" variant="secondary" onClick={sendVerificationCode} disabled={isSendingCode}>
              {isSendingCode ? "Sending..." : "Send code"}
            </Button>
          </div>

          <FormField label="Full name" error={errors.full_name?.message}>
            <Input placeholder="Your full name" {...register("full_name")} />
          </FormField>

          <FormField label="Nickname" error={errors.nickname?.message}>
            <Input placeholder="Displayed nickname" {...register("nickname")} />
          </FormField>

          <FormField label="Password" error={errors.password?.message}>
            <Input type="password" placeholder="At least 8 characters" {...register("password")} />
          </FormField>

          <div className="md:col-span-2">
            {sendCodeMessage ? <p className="mb-3 text-sm text-emerald-700">{sendCodeMessage}</p> : null}
            {errors.root?.message ? <p className="mb-3 text-sm text-red-600">{errors.root.message}</p> : null}
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "Creating..." : "Register and continue"}
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
}
