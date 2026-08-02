# M15：管理员认证与审核权限

## 状态

待验收。

## 模块目标

保护 M13 管理审核后台。未登录用户不能读取审核队列，也不能执行通过或驳回操作。
本期只提供管理员账号，不开放普通用户注册。

## 安全设计

- 管理员密码使用 Argon2 哈希，MySQL 不保存明文密码。
- 登录成功后签发 HS256 JWT 访问令牌。
- 令牌默认有效期为 480 分钟，可通过环境变量调整。
- 审核接口要求 `review_admin` 或 `super_admin` 角色。
- 前端令牌保存在 `sessionStorage`，关闭浏览器标签页后清除。
- 401 响应会清除本地管理会话。
- `AUTH_SECRET_KEY` 和初始密码只放在 `backend/.env`，不得提交 Git。

生产环境后续应增加 HTTPS、短期令牌刷新、登录限流和安全事件审计。

## 配置

在 `backend/.env` 中设置：

```env
AUTH_SECRET_KEY=一段足够长的随机字符串
AUTH_TOKEN_EXPIRE_MINUTES=480
```

不要继续使用 `.env.example` 中的占位密钥。

## 创建管理员

交互式创建或重置默认管理员：

```powershell
.\scripts\dev.ps1 admin-create
```

命令会在终端中安全提示输入密码，密码至少 8 位且不会显示。

如果终端不支持交互式密码输入，可临时在 `backend/.env` 设置：

```env
ADMIN_INITIAL_PASSWORD=仅用于首次创建的密码
```

创建完成后立即删除该环境变量并重启后端。

## 接口

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

以下接口现在需要 Bearer 令牌：

```text
GET  /api/v1/management/reviews
POST /api/v1/management/reviews/{record_id}/decision
```

## 前端

```text
http://127.0.0.1:5173/management/login
```

直接访问 `/management/reviews` 且没有管理会话时，会自动跳转到登录页。

## 验收

1. 配置新的 `AUTH_SECRET_KEY`。
2. 执行管理员创建命令并设置密码。
3. 重启项目。
4. 未登录访问审核 API，应返回 401。
5. 登录管理页面，确认能读取审核队列。
6. 点击退出登录，确认再次访问审核页面会跳转登录页。

## 当前不包含

- 普通旅行用户注册与登录。
- JWT 刷新令牌。
- 多因素认证。
- 密码找回。
- 登录失败限流与账号锁定。
