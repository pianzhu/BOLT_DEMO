# PRD: Python 项目结构（strands-agents + FastAPI）Demo

## 1. Introduction / Overview

在当前仓库内创建一个“主流且可扩展”的 Python 项目目录结构，技术栈使用 strands-agents + FastAPI。该结构用于团队协作与可维护性打基础，作为 demo 使用（不考虑部署、不要求可运行服务），但需为未来可能增加数据库等基础设施留下清晰扩展位。

## 2. Goals

- 提供清晰、通用的 Python 服务端目录结构，适配团队协作与后续扩展
- 明确分层与边界，支持未来加入数据库/缓存/队列等基础设施
- 预置代码质量与工程化占位（lint/test/CI 配置文件）
- 明确 tests 目录架构（unit/integration 与共享 fixture 约定）
- 仅创建目录与空占位文件，不实现业务逻辑或启动流程

## 3. User Stories

### US-001: 定义仓库顶层目录结构
**Description:** 作为团队成员，我希望仓库顶层结构清晰，以便快速理解项目组成与职责边界。

**Acceptance Criteria:**
- [ ] 创建并提交顶层目录：`app/`, `tests/`, `scripts/`, `docs/`, `infra/`, `configs/`, `tasks/`
- [ ] 顶层提供 `README.md` 与 `CONTRIBUTING.md` 占位文件（可为空或简短说明）
- [ ] 不新增任何可运行服务或业务代码

### US-002: 定义应用层目录结构（FastAPI + strands-agents）
**Description:** 作为后端开发者，我希望应用层结构清晰，以便未来按模块扩展 API 与 Agent。

**Acceptance Criteria:**
- [ ] 在 `app/` 内创建占位包：`api/`, `agents/`, `core/`, `services/`, `models/`, `repositories/`, `schemas/`
- [ ] 所有包均包含 `__init__.py`（可为空）
- [ ] 不实现路由、Agent 或业务逻辑

### US-003: 预留配置与环境管理结构
**Description:** 作为开发者，我希望配置结构统一，以便后续支持多环境与配置管理。

**Acceptance Criteria:**
- [ ] 创建 `configs/` 目录并包含 `dev/`, `test/`, `prod/` 子目录（占位）
- [ ] 提供 `configs/README.md` 或 `configs/.keep` 说明占位用途

### US-004: 预置工程化（lint/test/CI）占位
**Description:** 作为团队成员，我希望在结构中预留工程化配置位置，便于后续标准化。

**Acceptance Criteria:**
- [ ] 在仓库根目录创建以下占位文件：`pyproject.toml`, `pytest.ini`, `ruff.toml`, `mypy.ini`, `.pre-commit-config.yaml`
- [ ] 在 `.github/workflows/` 下创建 `ci.yml` 占位文件
- [ ] 文件允许为空或仅包含占位注释

### US-005: 定义测试目录结构（unit + integration）
**Description:** 作为团队成员，我希望测试目录结构清晰，以便后续补充单元与集成测试。

**Acceptance Criteria:**
- [ ] 在 `tests/` 下创建占位目录：`unit/`, `integration/`, `fixtures/`
- [ ] 在 `tests/` 下创建 `conftest.py` 与 `README.md`（可为空或简短约定说明）
- [ ] 不新增任何实际测试用例

## 4. Functional Requirements

- FR-1: 必须创建清晰的顶层目录结构以支撑后续扩展
- FR-2: `app/` 下需包含 API、Agent、核心模块、服务层、模型层、仓储层、数据结构层的占位包
- FR-3: 需提供多环境配置目录结构的占位
- FR-4: 需预置 lint/test/CI 的配置文件与目录占位
- FR-5: `tests/` 下需提供 unit/integration/fixtures 的基础结构占位
- FR-6: 不实现实际业务逻辑、路由或可运行服务

## 5. Non-Goals (Out of Scope)

- 不实现 FastAPI 启动、路由或示例 endpoint
- 不接入数据库、缓存、消息队列或外部服务
- 不配置实际部署或运行环境
- 不引入具体工程化工具的强制规则（仅占位）
- 不编写任何实际测试用例

## 6. Design Considerations (Optional)

- 目录命名采用通用团队习惯：`api/`, `services/`, `repositories/` 等
- 使用 `infra/` 作为未来数据库/外部依赖集成的占位

## 7. Technical Considerations (Optional)

- 技术栈明确为 strands-agents + FastAPI，但本次仅体现结构，不实现代码
- 未来数据库可能引入：优先落位于 `infra/` 与 `repositories/`
- 工程化配置建议集中在根目录，便于工具自动发现
- 工具选型已确定：lint/format 使用 Ruff，测试使用 pytest，类型检查使用 mypy，依赖管理使用 uv

## 8. Success Metrics

- 新成员在 5 分钟内可理解结构与职责分区
- Lint/Test/CI 占位文件齐全，满足后续规范化接入
- 未来加入数据库模块无需重构现有目录层级

## 9. Open Questions

- 是否需要额外的 `app/main.py` 占位（当前不在范围内）
