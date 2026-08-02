# M17 数据生命周期与归档预览

本模块只读统计达到保留期限的数据，为后续可恢复归档提供依据。

## 配置

可在 `backend/.env` 中配置天数（未配置时使用默认值）：

```env
RETENTION_INGESTION_DAYS=180
RETENTION_REVIEWS_DAYS=365
RETENTION_AI_SNAPSHOTS_DAYS=180
RETENTION_RECOMMENDATION_DAYS=365
```

## 使用

- 管理员接口：`GET /api/v1/management/data-retention/report`
- 命令行：`.\scripts\dev.ps1 retention-report`
- 运营看板会显示达到期限的记录数和截止日期。

报告不会删除、覆盖或移动数据。只有确认保留期限、导出格式和恢复策略后，才进入下一期可恢复归档实现。
