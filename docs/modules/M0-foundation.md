# M0：工程骨架与运行环境

## 状态

待验收。

## 目标

建立Vue 3、FastAPI、MySQL和Redis的最小可运行链路，为后续业务模块提供稳定基础。

## 已实现

- Vue 3、TypeScript、Vite、Vue Router与Pinia骨架。
- FastAPI版本化路由和生命周期管理。
- MySQL异步连接基础设施。
- Redis异步连接基础设施。
- 存活检查与依赖就绪检查。
- MySQL 8.4和Redis 7.4 Docker Compose配置。
- 前端环境状态页和基础响应式视觉。
- 前后端基础自动测试。
- 环境变量示例和启动说明。
- Makefile一键启动、停止、状态、日志和测试命令。
- 未安装Make时可直接使用的Windows启动与停止入口。

## 不包含

- 民宿业务数据表。
- 用户注册与登录。
- 平台数据接入。
- AI调用与推荐算法。
- 完整用户端和管理端页面。

## 实施验证结果

- 后端测试：3项通过。
- 后端静态检查与格式检查：通过。
- 前端测试：2项通过。
- 前端TypeScript检查与生产构建：通过。
- Docker Compose配置检查：通过。
- Redis 7.4容器健康检查：通过。
- FastAPI存活检查：通过。
- Vue开发服务器访问：通过。
- Vue到FastAPI的开发代理：通过。
- Vite固定绑定`127.0.0.1:5173`，避免本机IPv6回环地址无法访问：通过。
- 一键启动、重复启动、停止和再次启动：通过。
- MySQL 8.4与Redis 7.4真实容器健康检查：通过。
- FastAPI连接MySQL与Redis后的完整就绪检查：通过，返回HTTP 200。
- Windows免Make入口`start-dev.cmd`和`stop-dev.cmd`：通过。
- 桌面端和390px移动端浏览器检查：通过，无控制台错误。
- 依赖未就绪时返回503并显示具体状态：通过。

## 当前环境说明

本机未安装GNU Make，因此无法直接执行`make start`。Makefile的目标均调用同一个PowerShell脚本，当前环境已通过`start-dev.cmd`和脚本直接入口完成等价验证。安装Make后即可使用相同的`make`命令。

本机已有独立MySQL服务占用默认3306端口。为避免影响现有数据库，本项目的Docker MySQL固定映射到本机3307端口，后端默认连接配置已保持一致。

## 验收步骤

1. 按根目录README启动MySQL和Redis。
2. 启动FastAPI并访问存活与就绪检查。
3. 启动Vue并打开环境状态页。
4. 确认Vue、MySQL和Redis均显示“正常”。
5. 停止MySQL，重新检查并确认页面显示MySQL未就绪。
6. 重新启动MySQL，确认状态恢复。
7. 执行前端测试与构建。
8. 执行后端测试与静态检查。

## 通过条件

- 四项运行环境可以稳定启动。
- Vue可以通过代理访问FastAPI。
- FastAPI能准确检查MySQL与Redis状态。
- 自动测试与构建通过。
- 没有引入M0范围之外的业务实现。
