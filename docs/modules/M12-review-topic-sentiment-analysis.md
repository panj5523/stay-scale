# M12：评论主题与情绪分析

## 状态

待验收。

## 模块目标

接收来自美团、途家、木鸟等平台的结构化评论，保存可追溯的原文，再生成主题、情绪分布和证据短语。
平台采集模块只需要调用评论分析接口，不需要了解 DeepSeek 的请求格式。

## 接口

```text
POST /api/v1/listings/{listing_public_id}/review-analysis
```

请求一次最多 50 条评论，每条评论最多 2,000 字。`platform_code + external_id` 在同一民宿下唯一，
用于避免同一平台评论重复写入。

示例：

```json
{
  "reviews": [
    {
      "external_id": "mt-1001",
      "platform_code": "meituan",
      "content": "房间很干净，位置也方便",
      "rating": 4.8
    }
  ]
}
```

## AI 边界

- DeepSeek 只能引用输入评论中的短语，不能补充评论中没有的事实。
- 主题最多 8 个，情绪只能是 `positive`、`neutral` 或 `negative`。
- 情绪数量必须等于输入评论数量。
- 主题证据必须是原评论中的连续短语，否则触发本地降级。
- DeepSeek 未配置、网络失败或 JSON 校验失败时，使用关键词和评分进行本地初筛。
- 分析结果不修改民宿综合评分和推荐排序。

## MySQL 存储

`listing_reviews` 保存去重后的评论原文和来源字段；`review_analysis_snapshots` 保存每次分析的聚合结果、
主题证据、情绪计数和轻量 Token 审计。不会保存完整 Prompt 或模型原始响应。

为控制容量：

- 单条评论限制 2,000 字。
- 单次分析限制 50 条。
- 后续按民宿和月份归档旧评论原文，分析快照保留摘要。
- 删除民宿时评论及分析快照级联删除。

## 验收

1. 保持 `AI_PROVIDER=local`。
2. 启动项目并打开 FastAPI 文档。
3. 调用 `POST /api/v1/listings/{listing_id}/review-analysis`，提交 1～3 条中文评论。
4. 确认返回 `provider=local`、主题列表、情绪数量和“本地规则初筛”警告。
5. 使用相同 `platform_code + external_id` 再次提交时，确认接口提示重复来源，不产生重复评论。
6. 配置 DeepSeek 后使用新的评论批次，确认返回 `provider=deepseek`，且主题证据来自原评论。

## 当前不包含

- 平台评论自动抓取和登录态管理。
- 评论翻译。
- 用户对分析结果的手动修正界面。
- 基于评论自动修改推荐排序。
