# M9：DeepSeek AI 基础设施与需求解析升级

## 状态

待验收。

## 模块目标

在后端建立独立的 AI Provider 层，优先使用 DeepSeek 解析自然语言旅行需求；未配置 Key、请求超时、网络失败或输出校验失败时，自动回退到 M7 本地规则解析器。

本模块只接入“自然语言需求解析”，不同时接入推荐说明、旅行规划和评论分析。后续模块通过相同的 Provider 接口复用 DeepSeek 配置和审计能力。

## 配置

在 `backend/.env` 中配置，不要把 Key 写入代码、前端或 Git：

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
AI_TIMEOUT_SECONDS=20
```

默认配置为 `AI_PROVIDER=local`，适合没有 Key 的开发和测试环境。

DeepSeek 使用 OpenAI 兼容的 Chat Completions 接口。JSON 输出请求使用 `response_format: {"type": "json_object"}`，并要求提示词中明确出现 JSON 输出约束。

## 处理流程

```text
PreferenceParsingService
  ├── DeepSeek 已配置：DeepSeekPreferenceParser
  │       ↓ JSON 输出
  │   Pydantic 结构校验 + 原文证据检查
  └── 未配置或调用失败：ChinesePreferenceParser
          ↓
保存统一的解析会话
```

无论使用哪种解析器，用户都必须检查并确认，才能进入推荐引擎。

## 安全边界

- API Key 只存在后端环境变量。
- DeepSeek 不能直接访问 MySQL、修改民宿数据或决定最终排名。
- 模型输出必须符合结构化字段、日期、人数、预算和设施约束。
- `evidence.matched_text` 不在用户原文中时会被丢弃。
- DeepSeek 输出异常时使用本地规则，不阻断基础推荐功能。
- 不保存完整提示词和模型原文，避免扩大旅行需求数据留存范围。

## 调用审计

`preference_parse_sessions` 新增：

- `prompt_tokens`。
- `completion_tokens`。
- `total_tokens`。
- `ai_error_code`。

解析会话仍保存 Provider 名称和模型版本，便于对比 DeepSeek 与本地规则的结果。审计不保存 API Key。

## 测试

- DeepSeek JSON 输出可以转换为结构化偏好。
- 不属于用户原文的模型证据会被过滤。
- 非法 JSON 会触发校验错误并进入本地降级路径。
- 未配置 AI 时原有本地解析测试保持通过。
- HTTP、MySQL、前端和 M0 至 M8 回归测试保持通过。

## 无 Key 验收

1. 保持 `AI_PROVIDER=local` 或不配置 DeepSeek Key。
2. 启动项目并打开推荐页。
3. 识别默认自然语言需求。
4. 确认页面可以正常展示证据并生成推荐。
5. 查看解析会话的 `parser_name` 为 `local-rule-parser`。

## 有 Key 验收

1. 在后端 `.env` 设置 `AI_PROVIDER=deepseek` 和 `DEEPSEEK_API_KEY`。
2. 重启后端，不要把 Key 输入 Swagger 或前端页面。
3. 调用 `POST /api/v1/preference-parses`。
4. 确认返回的 `parser_name` 为 `deepseek`，`parser_version` 为实际模型名。
5. 确认结构化字段、证据和缺失项仍经过后端校验。
6. 临时让 DeepSeek 不可用，确认页面提示降级但手动推荐仍可使用。

## 不包含

- 推荐说明自然语言生成（后续模块）。
- 旅行计划草稿生成。
- 评论主题和情绪分析。
- 多轮对话记忆。
- 前端保存 API Key。
