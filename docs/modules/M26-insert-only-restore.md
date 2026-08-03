# M26 只新增事务恢复

M26 为已批准且通过 M25 安全闸门的申请提供事务恢复。

```text
POST /api/v1/management/data-retention/restore-requests/{public_id}/execute
Body: { "confirmation": "RESTORE INSERT ONLY" }
```

只有超级管理员可以执行。恢复仅使用 `INSERT`，不执行覆盖或删除；所有数据表在同一事务中提交，主键、外键或数据格式错误会触发整体回滚。成功后申请状态变为 `executed`。

建议仅在隔离的测试数据库中验收。旧申请没有申请时归档哈希快照，不能通过 M25 安全闸门，需要重新创建申请。
