# M19 归档包管理与完整性校验

M19 让管理员查看、校验并下载 M18 生成的归档包，不执行数据库删除或恢复写入。

## 接口

```text
GET  /api/v1/management/data-retention/archives
POST /api/v1/management/data-retention/archives/{archive_id}/verify
GET  /api/v1/management/data-retention/archives/{archive_id}/download
```

全部接口都要求管理员 Bearer Token。归档编号必须是合法 UUID，文件路径经过固定目录校验，不能通过路径参数访问归档目录之外的文件。

完整性校验会重新计算 SHA-256，并检查 ZIP 结构和 `manifest.json`。运营看板会显示文件大小、校验状态，并提供校验和下载按钮。
