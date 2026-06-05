# Dify 内容自动化管道 — 部署指南

## 概述

The Candid Care 内容管道通过 Dify Workflow 实现从 RSS 源到 Sanity CMS 的全自动内容生产：

```
[RSS Feed] → [AI 审核] → [AI 改写] → [AI 配图] → [Sanity 发布] → [Vercel 重建]
```

---

## 前置条件

### 1. 准备工作

| 条件 | 状态 | 获取方式 |
|------|------|----------|
| Dify 账号 (Cloud 或 Self-hosted) | 必须 | https://dify.ai |
| Sanity Project ID + API Token | 必须 | Sanity Dashboard → API |
| Sanity 中已完成初始配置 | 必须 | 至少一个 Author 和一个 Category 文档 |
| OpenAI API Key (或兼容) | 必须 | Dify 模型供应商配置 |
| AI 图片生成 API | 推荐 | 如 OpenAI DALL-E、Stability AI、Midjourney API |
| 2+ 个 RSS 健康类源 | 推荐 | 见下方推荐源列表 |

### 2. Sanity 初始化

在导入工作流前，确保 Sanity Studio 中已有：

```bash
# 1. 创建一个作者
# Sanity Studio → Author → 新建
# Name: "The Candid Care Editorial Team"
# 记下生成的 _id

# 2. 创建分类
# Sanity Studio → Category → 依次创建：
# - Nutrition (_id 备用)
# - Fitness
# - Mental Health
# - Sleep
# - Longevity
# - Lifestyle
# - Nutrition Facts
```

> **重要**: 记下 Author 的 `_id`（格式: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`），后续配置环境变量 `AUTHOR_REF_ID` 时使用。

### 3. Sanity API Token

1. 进入 [Sanity Dashboard](https://www.sanity.io/manage)
2. 选择项目 → **API** → **Tokens**
3. 点击 **Add API token**
4. Token name: `Dify Automation Pipeline`
5. Permissions: **Editor**
6. 复制生成的 Token → 配置到 Dify 环境变量 `SANITY_API_TOKEN`

---

## 导入工作流

### 方式一：从 DSL 导入（推荐）

1. 打开 Dify Studio → **创建应用** → **从 DSL 导入**
2. 上传 `dify/workflow.yml`
3. 应用自动创建，进入 **Workflow 编辑器**

### 方式二：手动构建

按照 `workflow.yml` 中的节点配置逐个创建。重点是：

- **RSS 采集** (Code 节点) — Python 解析多源 RSS
- **AI 改写** (LLM 节点) — 使用 `prompts/rewrite.md` 作为 System Prompt
- **Sanity 发布** (Code 节点) — 使用 `tools/sanity-api.py` 独立脚本

---

## 环境变量配置

在 Dify Workflow → **功能** → **环境变量** 中配置：

| 变量名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `RSS_FEED_URLS` | 文本 | 换行分隔的 RSS 源 | `https://www.health.harvard.edu/blog/feed` |
| `SANITY_PROJECT_ID` | 文本 | Sanity 项目 ID | `abc123def` |
| `SANITY_DATASET` | 文本 | Sanity 数据集 | `production` |
| `SANITY_API_TOKEN` | 密钥 | Sanity Editor Token | `sk...` |
| `AUTHOR_REF_ID` | 文本 | 默认作者 Sanity _id | `drafts.xxx-xxx` |
| `IMAGE_GEN_API_URL` | 文本 | 图片生成 API 地址 | `https://api.openai.com/v1/images/generations` |
| `IMAGE_GEN_API_KEY` | 密钥 | 图片生成 API Key | `sk-...` |
| `SITE_PUBLIC_URL` | 文本 | 站点公开地址 | `https://thecandidcare.com` |

---

## 推荐 RSS 源

以下为高质量健康与生活方式类 RSS 源：

### 健康与医学
- Harvard Health Blog: `https://www.health.harvard.edu/blog/feed`
- NIH News in Health: `https://newsinhealth.nih.gov/feed.xml`
- WHO News: `https://www.who.int/rss-feeds/news-english.xml`

### 睡眠
- Sleep Foundation: `https://www.sleepfoundation.org/feed`
- Sleep Doctor: `https://sleepdoctor.com/feed`

### 心理健康
- Psychology Today: `https://www.psychologytoday.com/us/blog/feed`
- Mindful: `https://www.mindful.org/feed`

### 营养
- NutritionFacts.org: `https://nutritionfacts.org/feed`
- Healthline Nutrition: `https://www.healthline.com/nutrition/feed`

### 长寿与生活方式
- Longevity Technology: `https://longevity.technology/feed`
- Blue Zones: `https://www.bluezones.com/feed`

---

## 触发与监控

### 定时触发

工作流默认每 **6 小时** 运行一次。修改频率：

1. 在 Dify Workflow 中点击 **开始** 节点
2. 修改 Cron 表达式：
   - 每 3 小时: `0 */3 * * *`
   - 每 6 小时: `0 */6 * * *`
   - 每日 9:00: `0 9 * * *`

### 手动触发

需要立即运行时，点击 **发布** → **运行** → **手动触发**。

### 日志与调试

1. 在 Dify 中找到本次运行的 **日志**
2. 查看每个节点的输入/输出
3. 重点检查:
   - `rss-fetch` — 是否成功抓取到文章
   - `article-review` — 审核决策是否合理
   - `article-rewrite` — 改写质量是否达标
   - `sanity-publish` — Sanity API 调用是否成功

---

## 完整管道流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Dify Workflow                                 │
│                                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │
│  │ 定时触发  │──▶│ RSS 采集  │──▶│ AI 审核   │──▶│ 是否通过?        │ │
│  │ (6h)     │   │ (多源)   │   │ (GPT-4o) │   │ quality ≥ 3     │ │
│  └──────────┘   └──────────┘   └──────────┘   └───────┬──────────┘ │
│                                                        │            │
│                                          ┌─────────────┘            │
│                                          ▼                          │
│                              ┌───────────────────────┐              │
│                              │      AI 改写           │              │
│                              │  (Candid Care 风格)    │              │
│                              └───────────┬───────────┘              │
│                                          ▼                          │
│                              ┌───────────────────────┐              │
│                              │    SEO/GEO 元数据      │              │
│                              │ (标题/FAQ/标签/摘要)    │              │
│                              └───────────┬───────────┘              │
│                                          ▼                          │
│                              ┌───────────────────────┐              │
│                              │     AI 配图生成        │              │
│                              │  (DALL-E / SD / etc)  │              │
│                              └───────────┬───────────┘              │
│                                          ▼                          │
│                              ┌───────────────────────┐              │
│                              │    Sanity 发布          │              │
│                              │ (上传图片 + 创建文档)   │              │
│                              └───────────┬───────────┘              │
└──────────────────────────────────────────┼──────────────────────────┘
                                           ▼
                              ┌───────────────────────┐
                              │   Sanity Webhook      │
                              │   → /api/revalidate   │
                              │   → Vercel Deploy     │
                              └───────────┬───────────┘
                                          ▼
                              ┌───────────────────────┐
                              │   Vercel 重新构建      │
                              │   站点更新上线         │
                              └───────────────────────┘
```

---

## 文件结构

```
dify/
├── README.md              ← 本文档
├── workflow.yml           ← Dify 工作流 DSL (导入用)
├── prompts/
│   ├── rewrite.md         ← AI 改写 System Prompt
│   ├── review.md          ← 内容审核 Prompt
│   └── seo-geo.md         ← SEO/GEO 元数据 Prompt
└── tools/
    └── sanity-api.py      ← Sanity API 独立工具脚本
```

---

## 常见问题

### Q: 图片生成 API 选哪个？

| 服务 | API 地址 | 风格 |
|------|---------|------|
| **DALL-E 3** | `https://api.openai.com/v1/images/generations` | 写实、高质量 |
| **Stability AI** | `https://api.stability.ai/v1/generation/...` | 可控性强 |
| **Midjourney** | 需第三方 API 中转 | 艺术感强 |

> 推荐 DALL-E 3 作为起步，配置最简单。

### Q: 如何避免重复发布同一篇文章？

RSS 节点的去重逻辑基于 `source_url`，同一来源 24 小时内只处理一次。

### Q: 如何调整改写风格？

修改 `prompts/rewrite.md` 中的 Brand Voice Guidelines，然后在 Dify 中更新 LLM 节点的 System Prompt。

### Q: 构建失败怎么办？

1. 检查 Dify 运行日志 → 定位失败节点
2. 常见原因:
   - RSS 源不可达 → 更换源或添加备用源
   - Sanity Token 过期 → 重新生成
   - 图片 API 配额不足 → 检查 API 用量
   - 分类 slug 不匹配 → 检查 Sanity 中分类的 slug
