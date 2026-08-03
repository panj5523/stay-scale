# M22 归档恢复审批与审计

M22 为后续真正恢复数据建立审批申请记录。管理员提交归档恢复申请后，系统将 M21 恢复计划快照保存到 MySQL，状态为 `pending`。

接口：

```text
POST /api/v1/management/data-retention/restore-requests
Body: { "archive_id": "..." }
```

申请只允许针对已有归档包创建，并且会保存申请人、归档编号和冲突分析快照。当前版本不会执行恢复，也没有自动批准逻辑；后续模块再增加审批列表、驳回原因、审批人和真正恢复执行。
