"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { apiFetch, saveAuthTokens } from "@/lib/api";


const schema = z.object({
  email: z.string().email("请输入合法邮箱"),
  password: z.string().min(8, "密码至少 8 位"),
});

type FormValues = z.infer<typeof schema>;

type LoginResponse = {
  access: string;
  refresh: string;
};

export function LoginForm() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      const response = await apiFetch<LoginResponse>("auth/login/", {
        method: "POST",
        auth: false,
        body: JSON.stringify(values),
      });
      saveAuthTokens(response.access, response.refresh);
      startTransition(() => {
        router.push("/dashboard");
      });
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "登录失败" });
    }
  });

  return (
    <Card className="mx-auto w-full max-w-lg bg-shell/95">
      <div className="space-y-6">
        <div className="space-y-2 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">Account Access</p>
          <h1 className="font-serif text-3xl text-ink">登录 PairUp</h1>
          <p className="text-sm text-slate-500">用邮箱进入你的校园关系与协作工作台。</p>
        </div>

        <form className="space-y-4" onSubmit={onSubmit}>
          <FormField label="邮箱" error={errors.email?.message}>
            <Input type="email" placeholder="name@university.edu.cn" {...register("email")} />
          </FormField>
          <FormField label="密码" error={errors.password?.message}>
            <Input type="password" placeholder="至少 8 位" {...register("password")} />
          </FormField>
          {errors.root?.message ? <p className="text-sm text-red-600">{errors.root.message}</p> : null}
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? "登录中..." : "登录并进入控制台"}
          </Button>
        </form>

        <p className="text-center text-sm text-slate-500">
          还没有账号？
          <Link className="ml-2 font-semibold text-coral" href="/register">
            去注册
          </Link>
        </p>
      </div>
    </Card>
  );
}
