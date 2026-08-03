# M27 恢复执行审计与结果追踪

M27 将成功恢复的执行结果持久化到 `archive_restore_requests`。

新增审计字段：

- `executed_by`：执行管理员
- `executed_at`：执行时间
- `execution_summary`：归档 SHA-256、各表新增数量、总新增数量、覆盖和删除标记

审计字段与恢复数据在同一事务中提交。事务失败时整体回滚，不会把失败任务标记为 `executed`。恢复审批页面会展示成功执行的新增数量和时间。
