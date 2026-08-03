# M23 恢复申请审批

M23 增加恢复申请的审批闭环，审批只改变 `archive_restore_requests` 状态，不恢复归档数据。

接口：

```text
GET   /api/v1/management/data-retention/restore-requests
PATCH /api/v1/management/data-retention/restore-requests/{public_id}
Body: { "action": "approved", "reason": "已完成备份确认" }
```

`review_admin` 可以查看申请，只有 `super_admin` 可以批准或驳回。申请只能从 `pending` 变为 `approved` 或 `rejected`，重复审批会返回冲突错误。后续模块才会消费已批准申请并执行真正的数据恢复。
