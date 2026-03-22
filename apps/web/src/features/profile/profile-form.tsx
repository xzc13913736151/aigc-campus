"use client";

import { useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch, getAccessToken } from "@/lib/api";


const schema = z.object({
  headline: z.string().max(120),
  bio: z.string().max(500),
  gender: z.string().min(1),
  major: z.string().max(120),
  grade: z.string().max(40),
  interestsText: z.string(),
});

type FormValues = z.infer<typeof schema>;

type ProfileResponse = {
  avatar_url: string;
  headline: string;
  bio: string;
  gender: string;
  major: string;
  grade: string;
  interests: string[];
};

export function ProfileForm() {
  const hasToken = Boolean(getAccessToken());
  const {
    register,
    reset,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      headline: "",
      bio: "",
      gender: "unknown",
      major: "",
      grade: "",
      interestsText: "",
    },
  });

  const profileQuery = useQuery({
    queryKey: ["profile", "me"],
    queryFn: () => apiFetch<ProfileResponse>("profile/me/"),
    enabled: hasToken,
  });

  useEffect(() => {
    if (profileQuery.data) {
      reset({
        headline: profileQuery.data.headline ?? "",
        bio: profileQuery.data.bio ?? "",
        gender: profileQuery.data.gender ?? "unknown",
        major: profileQuery.data.major ?? "",
        grade: profileQuery.data.grade ?? "",
        interestsText: (profileQuery.data.interests ?? []).join(", "),
      });
    }
  }, [profileQuery.data, reset]);

  const mutation = useMutation({
    mutationFn: (payload: Omit<ProfileResponse, "avatar_url">) =>
      apiFetch<ProfileResponse>("profile/me/", {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await mutation.mutateAsync({
        headline: values.headline,
        bio: values.bio,
        gender: values.gender,
        major: values.major,
        grade: values.grade,
        interests: values.interestsText
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "保存失败" });
    }
  });

  if (!hasToken) {
    return <EmptyState title="请先登录" description="个人资料页需要 JWT 登录态。完成注册或登录后，再回到这里编辑你的校园档案。" />;
  }

  return (
    <Card className="space-y-6">
      <div className="space-y-2">
        <h1 className="font-serif text-3xl text-ink">个人资料</h1>
        <p className="text-sm text-slate-500">这一页连接后端真实接口，用来打通注册后第一条资料编辑链路。</p>
      </div>

      <form className="grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
        <FormField label="一句话介绍" error={errors.headline?.message}>
          <Input placeholder="比如：南开大三，偏产品和数据" {...register("headline")} />
        </FormField>
        <FormField label="性别" error={errors.gender?.message}>
          <Input placeholder="male / female / other / unknown" {...register("gender")} />
        </FormField>
        <FormField label="专业" error={errors.major?.message}>
          <Input placeholder="计算机科学与技术" {...register("major")} />
        </FormField>
        <FormField label="年级" error={errors.grade?.message}>
          <Input placeholder="2023 级 / 大三" {...register("grade")} />
        </FormField>
        <div className="md:col-span-2">
          <FormField label="兴趣标签" description="用英文逗号分隔" error={errors.interestsText?.message}>
            <Input placeholder="产品, 摄影, 跑步, 保研" {...register("interestsText")} />
          </FormField>
        </div>
        <div className="md:col-span-2">
          <FormField label="个人简介" error={errors.bio?.message}>
            <Textarea placeholder="介绍你的目标、偏好和擅长的事" {...register("bio")} />
          </FormField>
        </div>
        {errors.root?.message ? <p className="md:col-span-2 text-sm text-red-600">{errors.root.message}</p> : null}
        <div className="md:col-span-2 flex justify-end">
          <Button type="submit" disabled={isSubmitting || mutation.isPending || profileQuery.isLoading}>
            {mutation.isPending ? "保存中..." : "保存资料"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
