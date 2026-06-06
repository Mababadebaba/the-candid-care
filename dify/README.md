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
| Dify 账号 (Cloud 或 Self-hosted) | 必须 | https://cloud.dify.ai |
| Sanity Project ID + API Token | ✅ 已配 | o06jwzs8, Token 需填入 |
| Sanity 初始内容 | ✅ 已创建 | Author + 7 Categories |
| DeepSeek API Key | 必须 | https://platform.deepseek.com/api_keys |
| 图片生成 | ✅ 内置 | 自动生成暖色渐变 SVG 占位图 |
| 4 个 RSS 健康类源 | ✅ 已配 | Harvard Health, Sleep Foundation 等 |

### 2. Sanity 初始化 ✅ 已完成

Author 和 7 个 Category 已自动创建：

- **Author**: Dr. Emma Chen (`author-default`)
- **Categories**: Mindfulness, Nutrition, Movement, Sleep, Mental Health, Relationships, Self-Care

### 3. DeepSeek API Key (唯一需要获取的新 Key)

1. 打开 https://platform.deepseek.com/api_keys → 登录
2. 点 **创建 API key** → 复制 `sk-...`
3. 记下这个 Key，后续在 Dify 配置模型供应商时使用

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

导入 workflow.yml 后，大部分变量已预填。只需在 Dify → **功能** → **环境变量** 中更新：

| 变量名 | 类型 | 当前状态 | 说明 |
|--------|------|----------|------|
| `RSS_FEED_URLS` | 文本 | ✅ 已填 | 4 个健康类 RSS 源 |
| `SANITY_PROJECT_ID` | 文本 | ✅ 已填 `o06jwzs8` | Sanity 项目 ID |
| `SANITY_DATASET` | 文本 | ✅ 已填 `production` | Sanity 数据集 |
| `SANITY_API_TOKEN` | 密钥 | ⚠️ 需填入 | 你之前创建的 Sanity Token |
| `AUTHOR_REF_ID` | 文本 | ✅ 已填 `author-default` | 默认作者引用 |
| `SITE_PUBLIC_URL` | 文本 | ✅ 已填 | `https://the-candid-care.vercel.app` |

> 只需要填 **1 个**变量：`SANITY_API_TOKEN`（你在 Sanity 后台创建的 Token）。

### 配置 DeepSeek 模型供应商

这是最重要的一步：
1. Dify 右上角头像 → **设置** → **模型供应商**
2. 找到 **DeepSeek** → 点击 → **添加**
3. 填入你的 DeepSeek API Key → **保存**

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

### Q: 图片怎么处理？

工作流内置了占位图生成：自动创建一张暖色调渐变的 SVG 图片（品牌色 `#1C1A17 → #A16207 → #FAFAF8`）作为文章封面。后续如需接入 AI 图片生成（DALL-E 等），在工作流中加一个 HTTP 节点即可。

### Q: 如何避免重复发布同一篇文章？

去重基于 `source_url`，同一来源在全量数据中只处理一次（RSS 节点 24h 窗口内去重）。

### Q: 如何调整改写风格？

修改 `prompts/rewrite.md` 中的 Brand Voice Guidelines，然后在 Dify LLM 节点中更新 System Prompt。

### Q: DeepSeek 和 OpenAI 有什么区别？

DeepSeek 的 API 完全兼容 OpenAI 格式，价格更低（约 ¥1/百万 token）。本次改写任务用 `deepseek-chat` 模型，效果与 GPT-4o 相当。

### Q: 构建失败怎么办？

1. 检查 Dify 运行日志 → 定位失败节点
2. 常见原因:
   - RSS 源不可达 → 更换源或添加备用源
   - Sanity Token 过期 → 重新生成
   - DeepSeek 余额不足 → 充值或切换模型
   - 分类 slug 不匹配 → 检查 Sanity 中分类的 slug
