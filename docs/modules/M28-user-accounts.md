# M28 用户账户与个人中心

M28 第一期增加普通用户注册、登录、个人资料和收藏民宿。

前端页面：`/account`

主要接口：

```text
POST   /api/v1/users/auth/register
POST   /api/v1/users/auth/login
GET    /api/v1/users/me
GET    /api/v1/users/me/favorites
PUT    /api/v1/users/me/favorites/{listing_public_id}
DELETE /api/v1/users/me/favorites/{listing_public_id}
```

普通用户 Token 类型为 `user_access`，管理员 Token 类型为 `admin_access`，两者不能互相访问对方的受保护接口。密码使用与管理员相同的安全哈希算法保存，数据库不保存明文密码。
