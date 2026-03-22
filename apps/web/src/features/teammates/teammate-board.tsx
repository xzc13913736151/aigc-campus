"use client";

import { useDeferredValue, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { FilterBar } from "@/components/ui/filter-bar";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { List } from "@/components/ui/list";
import { Pagination } from "@/components/ui/pagination";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch, getAccessToken } from "@/lib/api";


const schema = z.object({
  title: z.string().min(4, "标题至少 4 个字符"),
  summary: z.string().min(8, "摘要至少 8 个字符"),
  details: z.string().min(20, "正文至少 20 个字符"),
  target_size: z.number().int().min(2).max(20),
  tagsText: z.string(),
});

type FormValues = z.infer<typeof schema>;

type TeamPost = {
  id: string;
  title: string;
  summary: string;
  details: string;
  tags: string[];
  required_skills: string[];
  target_size: number;
  current_size: number;
  author: {
    email: string;
    nickname: string;
    full_name: string;
  };
};

export function TeammateBoard() {
  const queryClient = useQueryClient();
  const hasToken = Boolean(getAccessToken());
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      summary: "",
      details: "",
      target_size: 3,
      tagsText: "",
    },
  });

  const postsQuery = useQuery({
    queryKey: ["teammates", deferredQuery],
    queryFn: () =>
      apiFetch<TeamPost[]>(`teammates/posts/${deferredQuery ? `?q=${encodeURIComponent(deferredQuery)}` : ""}`, {
        auth: false,
      }),
  });

  const createMutation = useMutation({
    mutationFn: (values: FormValues) =>
      apiFetch<TeamPost>("teammates/posts/", {
        method: "POST",
        body: JSON.stringify({
          title: values.title,
          summary: values.summary,
          details: values.details,
          target_size: values.target_size,
          tags: values.tagsText
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean),
        }),
      }),
    onSuccess: async () => {
      reset();
      await queryClient.invalidateQueries({ queryKey: ["teammates"] });
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await createMutation.mutateAsync(values);
    } catch (error) {
      setError("root", { message: error instanceof Error ? error.message : "发布失败" });
    }
  });

  return (
    <div className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
      <section className="space-y-4">
        <FilterBar value={query} onChange={setQuery} placeholder="搜索组队关键词，例如 保研 / 数模 / 黑客松" />
        {postsQuery.data?.length ? (
          <List>
            {postsQuery.data.map((post) => (
              <Card key={post.id} className="bg-white/90">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-xl font-semibold text-ink">{post.title}</h3>
                      <p className="mt-1 text-sm text-slate-500">{post.summary}</p>
                    </div>
                    <div className="rounded-full bg-canvas px-3 py-2 text-sm text-slate-600">
                      {post.current_size} / {post.target_size}
                    </div>
                  </div>
                  <p className="text-sm leading-7 text-slate-600">{post.details}</p>
                  <div className="flex flex-wrap gap-2">
                    {post.tags?.map((tag) => (
                      <span key={tag} className="rounded-full bg-canvas px-3 py-1 text-xs font-medium text-ink">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </List>
        ) : (
          <EmptyState title="还没有组队帖" description="你可以先用右侧表单发出第一条找队友需求，随后它会出现在这里。" />
        )}
        <Pagination />
      </section>

      <section>
        <Card className="sticky top-28 space-y-5 bg-shell">
          <div className="space-y-2">
            <h2 className="font-serif text-2xl text-ink">发布组队帖</h2>
            <p className="text-sm text-slate-500">这部分直接连接后端 `/api/v1/teammates/posts/`，用于打通 MVP 的一次真实行为。</p>
          </div>

          {!hasToken ? (
            <EmptyState title="请先登录" description="登录后才能发布组队帖。列表仍然可以匿名查看。" />
          ) : (
            <form className="space-y-4" onSubmit={onSubmit}>
              <FormField label="标题" error={errors.title?.message}>
                <Input placeholder="例如：找 2 位一起做夏令营产品作品集" {...register("title")} />
              </FormField>
              <FormField label="摘要" error={errors.summary?.message}>
                <Input placeholder="一句话说明你在找什么样的队友" {...register("summary")} />
              </FormField>
              <FormField label="详细说明" error={errors.details?.message}>
                <Textarea placeholder="补充时间线、技能要求、合作方式、目前进度等" {...register("details")} />
              </FormField>
              <FormField label="目标人数" error={errors.target_size?.message}>
                <Input type="number" min={2} max={20} {...register("target_size", { valueAsNumber: true })} />
              </FormField>
              <FormField label="标签" description="逗号分隔" error={errors.tagsText?.message}>
                <Input placeholder="保研, 产品, 算法, 校园项目" {...register("tagsText")} />
              </FormField>
              {errors.root?.message ? <p className="text-sm text-red-600">{errors.root.message}</p> : null}
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? "发布中..." : "发布组队帖"}
              </Button>
            </form>
          )}
        </Card>
      </section>
    </div>
  );
}
