# M18 可恢复归档执行

M18 在 M17 预览基础上生成 JSONL 压缩归档包，但不删除热表数据。

## 管理员接口

```text
POST /api/v1/management/data-retention/archive
Body: { "confirm": true }
```

接口需要管理员 Bearer Token。未明确传入 `confirm=true` 时会拒绝执行。返回归档文件名、各表导出数量和 SHA-256 校验值。

默认输出目录为 `backend/.runtime/archives`（可通过 `ARCHIVE_OUTPUT_DIR` 调整），每张表最多导出 `ARCHIVE_MAX_RECORDS_PER_TABLE` 条，超过上限会在返回结果中提示截断。

运营看板提供同样的确认按钮。归档包包含 `manifest.json` 和各表的 `data/<table>.jsonl` 文件；`deletion_performed` 始终为 `false`。后续若要清理热表，需要另行确认删除策略、备份策略和恢复演练。
