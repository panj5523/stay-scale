# M21 恢复冲突分析与执行计划

M21 将归档中的主键与当前 MySQL 数据比较，生成只读恢复计划。

```text
GET /api/v1/management/data-retention/archives/{archive_id}/restore-plan
```

计划包含每张表的归档记录数、可新增数量、已有主键冲突、无效记录，以及外键依赖下的建议执行顺序。归档缺表、主键冲突或无效记录都会形成阻断原因。

接口的 `restore_performed` 始终为 `false`，不会执行 INSERT、UPDATE 或 DELETE。运营看板的“冲突分析”按钮会显示可新增数量或冲突数量。
