"use client";

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
  full_name: z.string().min(2, "姓名至少 2 个字符"),
  nickname: z.string().min(2, "昵称至少 2 个字符"),
  password: z.string().min(8, "密码至少 8 位"),
});

type FormValues = z.infer<typeof schema>;

type LoginResponse = {
  access: string;
  refresh: string;
};

export function RegisterForm() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = handleSubmit(async (values) => {
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
      setError("root", { message: error instanceof Error ? error.message : "注册失败" });
    }
  });

  return (
    <Card className="mx-auto w-full max-w-2xl bg-shell/95">
      <div className="space-y-6">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">Onboarding</p>
          <h1 className="font-serif text-3xl text-ink">创建账号并补齐校园档案</h1>
          <p className="text-sm text-slate-500">首版默认使用邮箱 + 密码。后续再叠加学校邮箱验证。</p>
        </div>

        <form className="grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
          <FormField label="邮箱" error={errors.email?.message}>
            <Input type="email" placeholder="name@university.edu.cn" {...register("email")} />
          </FormField>
          <FormField label="姓名" error={errors.full_name?.message}>
            <Input placeholder="真实姓名或常用名称" {...register("full_name")} />
          </FormField>
          <FormField label="昵称" error={errors.nickname?.message}>
            <Input placeholder="在平台展示的昵称" {...register("nickname")} />
          </FormField>
          <FormField label="密码" error={errors.password?.message}>
            <Input type="password" placeholder="至少 8 位" {...register("password")} />
          </FormField>
          <div className="md:col-span-2">
            {errors.root?.message ? <p className="mb-3 text-sm text-red-600">{errors.root.message}</p> : null}
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "创建中..." : "注册并进入资料页"}
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
}
