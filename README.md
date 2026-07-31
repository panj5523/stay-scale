# Stay Scale

民宿智能推荐、跨平台比价与旅行规划平台。当前已完成M0工程骨架，包含Vue 3前端、FastAPI后端、MySQL和Redis运行环境。

## 环境要求

- Node.js 22或更高版本
- Python 3.12或更高版本
- Docker Desktop与Docker Compose

## 一键启动

如果已经安装GNU Make，在项目根目录执行：

```powershell
make start
```

当前Windows电脑如果没有安装Make，可以直接双击`start-dev.cmd`，或执行：

```powershell
.\start-dev.cmd
```

启动脚本会依次检查并启动Docker Desktop、MySQL、Redis、FastAPI和Vue，等待服务就绪后显示访问地址。停止全部服务并保留数据库数据：

```powershell
make stop
```

未安装Make时执行：

```powershell
.\stop-dev.cmd
```

其他命令：

```text
make status   查看服务状态
make logs     查看最近日志
make restart  重启全部服务
make test     执行前后端测试和构建
make install  安装缺失依赖
```

## 1. 启动MySQL和Redis

在项目根目录执行：

```powershell
docker compose up -d mysql redis
docker compose ps
```

首次启动MySQL可能需要约30秒完成初始化。

项目默认将容器内的MySQL映射到本机`3307`端口，避免与本机已有的MySQL服务冲突。

## 2. 启动FastAPI

首次运行：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

后续运行只需要激活虚拟环境并启动服务：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

接口地址：

- API文档：http://127.0.0.1:8000/docs
- 存活检查：http://127.0.0.1:8000/api/v1/health/live
- 就绪检查：http://127.0.0.1:8000/api/v1/health/ready

## 3. 启动Vue前端

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

打开：http://127.0.0.1:5173

## 测试

后端：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
ruff check .
```

前端：

```powershell
cd frontend
npm test
npm run build
```

## 停止基础服务

```powershell
docker compose stop mysql redis
```

`docker compose stop`只停止容器，不删除MySQL和Redis数据。

## 当前范围

M0只验证项目运行环境，不包含民宿业务表、AI模型调用、推荐算法或业务页面。下一模块需要在M0通过验收后才能开始。
