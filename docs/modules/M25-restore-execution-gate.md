# M25 恢复执行安全闸门

M25 在真正恢复数据前执行最后一次只读安全检查。

```text
GET /api/v1/management/data-retention/restore-requests/{public_id}/execution-readiness
```

安全闸门检查申请是否已批准、归档 ZIP 是否完整、SHA-256 是否与申请时一致、恢复计划是否变化，以及当前 MySQL 是否仍无冲突。申请人不能审批自己的恢复申请，执行前检查仅限超级管理员。

返回的 `execution_performed` 始终为 `false`。检查通过只代表具备进入事务恢复模块的条件，不会自动写入数据库。
