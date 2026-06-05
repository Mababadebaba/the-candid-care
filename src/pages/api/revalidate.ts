/**
 * Sanity Webhook → Vercel Deploy Hook
 *
 * 当 Sanity CMS 内容变更时，Sanity 发送 Webhook 到此端点。
 * 验证通过后，调用 Vercel Deploy Hook 触发站点重新构建。
 *
 * 环境变量：
 *   SANITY_WEBHOOK_SECRET  — Sanity Webhook 共享密钥
 *   VERCEL_DEPLOY_HOOK_URL — Vercel Deploy Hook URL
 */

import type { APIRoute } from "astro";

// 标记为服务端渲染端点 (不预渲染)
export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  const webhookSecret = import.meta.env.SANITY_WEBHOOK_SECRET;
  const deployHookUrl = import.meta.env.VERCEL_DEPLOY_HOOK_URL;

  // 生产环境必须配置密钥
  if (!webhookSecret || !deployHookUrl) {
    return new Response(
      JSON.stringify({
        error: "Server misconfigured: missing SANITY_WEBHOOK_SECRET or VERCEL_DEPLOY_HOOK_URL",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // 验证请求方法
  if (request.method !== "POST") {
    return new Response(
      JSON.stringify({ error: "Method not allowed" }),
      { status: 405, headers: { "Content-Type": "application/json" } }
    );
  }

  try {
    const body = await request.json();

    // 支持两种 Sanity Webhook 验证方式
    // 方式 1：Header 中的 Authorization Bearer token
    const authHeader = request.headers.get("authorization");
    const bearerToken = authHeader?.startsWith("Bearer ") ? authHeader.slice(7) : null;

    // 方式 2：Body 中的 _secret 字段 (Sanity 旧版 Webhook)
    const bodySecret = body?._secret;

    const providedSecret = bearerToken || bodySecret;

    if (!providedSecret || providedSecret !== webhookSecret) {
      return new Response(
        JSON.stringify({ error: "Unauthorized: invalid webhook secret" }),
        { status: 401, headers: { "Content-Type": "application/json" } }
      );
    }

    // 可选：按文档类型过滤
    // 只在文章、作者或分类变更时触发重建
    const allowedTypes = ["article", "author", "category"];
    const docType = body?._type;

    if (docType && !allowedTypes.includes(docType)) {
      return new Response(
        JSON.stringify({
          skipped: true,
          reason: `Document type "${docType}" does not trigger rebuild`,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    // 调用 Vercel Deploy Hook 触发重建
    const deployResponse = await fetch(deployHookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!deployResponse.ok) {
      console.error(
        `[revalidate] Vercel Deploy Hook failed: ${deployResponse.status} ${deployResponse.statusText}`
      );
      return new Response(
        JSON.stringify({
          error: "Deploy hook call failed",
          status: deployResponse.status,
        }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }

    const deployResult = await deployResponse.json();

    return new Response(
      JSON.stringify({
        revalidated: true,
        message: "Rebuild triggered successfully",
        deploy: deployResult,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (err) {
    console.error("[revalidate] Unexpected error:", err);
    return new Response(
      JSON.stringify({
        error: "Internal server error",
        message: err instanceof Error ? err.message : "Unknown error",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
};
