# M20 归档恢复预览与演练校验

M20 在真正恢复数据前读取归档 ZIP，检查 `manifest.json`、JSONL 表文件、记录数量和 ZIP 完整性。

接口：

```text
GET /api/v1/management/data-retention/archives/{archive_id}/restore-preview
```

接口只读，`restore_performed` 始终为 `false`，不会向 MySQL 写入、更新或覆盖任何数据。运营看板的“恢复预览”按钮用于查看预计恢复记录数和缺失表提醒。只有完成恢复策略、字段映射、冲突处理和备份确认后，才进入真正恢复模块。
