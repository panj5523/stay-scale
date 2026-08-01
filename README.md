# Stay Scale

## M9 DeepSeek AI 基础设施

M9 为后端增加独立的 AI Provider 层。配置 DeepSeek 后，需求解析会优先调用 DeepSeek JSON 输出；没有 Key、网络失败或输出不合格时自动回退到本地规则。默认仍是 `AI_PROVIDER=local`，不会影响现有运行环境。

配置和验收方式见 `docs/modules/M9-deepseek-ai-foundation.md`。API Key 只能写入后端 `.env`，不能提交到 GitHub 或放入 Vue 前端。

## M8 推荐解释与反馈调整

M8 为推荐结果补充妥协与风险说明，并支持用户输入“想便宜一点”“更想看海”“住双廊镇”等反馈。系统把反馈转换成受支持的偏好字段，重新调用推荐引擎并保存调整前后会话。

调整接口为 `POST /api/v1/recommendations/{session_id}/adjust`，详细边界和验收方式见 `docs/modules/M8-recommendation-feedback.md`。

## M7 自然语言需求解析与确认

M7 在推荐页增加中文自然语言输入。系统会提取城市、日期、人数、预算、设施、区域和旅行风格，展示证据与置信度，用户检查修改并确认后才进入推荐计算。

当前使用不依赖外部 API Key 的本地可解释解析器。接口位于 `POST /api/v1/preference-parses`，详细规则和验收步骤见 `docs/modules/M7-natural-language-preferences.md`。

## 民宿数据新增流程

民宿数据统一经过 M4 导入、归一化和匹配，再由后续 M13 管理审核后台确认后进入查询和推荐。开发阶段支持 JSON/CSV 演示文件，正式阶段优先使用官方/联盟 API、商家授权数据或正式合作接口；不采用未经授权的网页抓取。流程说明见 `docs/modules/M4-platform-ingestion.md` 和 `docs/modules/M13-management-review.md`。

## M6 前端个性化推荐体验

M6 将可解释推荐能力接入 Vue 3。启动项目后打开 `http://127.0.0.1:5173/recommendations`，可以填写日期、人数和总预算，选择旅行风格、设施及区域偏好，并查看推荐排序、理由与五项分数。

页面支持桌面端和移动端，包含加载、失败、无候选和成功状态。详细验收方式见 `docs/modules/M6-frontend-recommendations.md`。

## M5 可解释个性化推荐

M5 根据预算、旅行风格、设施和区域偏好，对实时可订候选计算价格、评分、设施、平台覆盖和位置得分，并保存可复查的推荐会话。

```http
POST /api/v1/recommendations
GET /api/v1/recommendations/{session_id}
```

接口可以在 `http://127.0.0.1:8000/docs` 的 `recommendations` 分组验收。详细评分规则见 `docs/modules/M5-explainable-recommendations.md`。

## M4 平台数据接入与归一化

M4 增加平台适配器、字段归一化、同店匹配和完整导入审计。当前使用本地途家风格演示 JSON，不直接抓取真实平台页面。

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts\dev.ps1 data-import
```

导入批次可在 FastAPI 文档的 `ingestion` 分组查看。详细边界和验收步骤见 `docs/modules/M4-platform-ingestion.md`。

## M3 前端搜索与比价页面

启动项目后打开 `http://127.0.0.1:5173/`，可以使用大理演示数据完成民宿搜索、设施和价格筛选，并打开跨平台报价详情。原运行环境状态页移动到 `http://127.0.0.1:5173/status`。

M3 的功能边界和验收步骤见 `docs/modules/M3-frontend-comparison.md`。

## M2 民宿查询与比价 API

启动项目后，可通过 FastAPI 文档测试查询与报价接口：

- API 文档：`http://127.0.0.1:8000/docs`
- 搜索接口：`GET /api/v1/listings`
- 报价详情：`GET /api/v1/listings/{public_id}`

演示数据使用“大理市”、入住日期 `2026-10-02`、离店日期 `2026-10-05` 和 2 位住客。详细参数与验收方式见 `docs/modules/M2-listing-comparison-api.md`。

## M1 数据库命令

一键启动会自动应用 Alembic 迁移，并以幂等方式初始化演示数据。也可以单独执行：

```powershell
make db-migrate
make db-seed
```

当前 Windows 环境未安装 Make 时，使用等价命令：

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts\dev.ps1 db-migrate
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts\dev.ps1 db-seed
```

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
