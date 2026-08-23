# 贡献指南

本项目采用一条最小协作路径：

`同步 main → 创建短分支 → 修改与检查 → 提交 → 推送 → Pull Request → 他人评审 → 合并 → 再次同步 main`

初次参与时，使用 GitHub Desktop 完成 Git 操作；可以让 Codex 帮助理解项目、修改文件和执行检查，但提交、推送、评审与合并由成员确认。

## 开始前

1. 安装并登录 GitHub Desktop。
2. 从 GitHub 克隆本仓库，不要下载 ZIP 作为工作副本。
3. 阅读 [README.md](README.md)，确认任务确实属于本项目。
4. 不要把账号、令牌、密码、个人资料或其他敏感信息写入仓库。

## 完成一次修改

### 1. 同步主线

在 GitHub Desktop 中切换到 `main`，依次点击 `Fetch origin`；如果出现 `Pull origin`，继续点击它。

开始新任务前，应确认当前分支是 `main`，并且界面显示 `No local changes`。

### 2. 创建短分支

一个任务只使用一个分支，不直接在 `main` 上修改。

分支名使用简短英文，例如：

- 新功能：`feat/add-campus-map`
- 修复：`fix/correct-office-hours`
- 文档：`docs/update-install-guide`
- Codex 辅助任务：`codex/update-freshman-guide`

### 3. 修改并检查

可以把任务交给 Codex，但应明确限制范围。例如：

```text
请先阅读 README.md，只修改 docs/guide.md，补充一段安装说明。
不要修改其他文件，不要提交，不要推送。完成后说明改动并运行适用检查。
```

Codex 完成后，在 GitHub Desktop 的 `Changes` 中逐项检查：

- 是否只改了任务要求的文件；
- 新增和删除的内容是否正确；
- 是否混入密钥、缓存、生成文件或无关格式化；
- 文档链接、命令或代码检查是否通过。

### 4. 提交

确认变更后再提交。提交说明应简短并说明结果，例如：

- `docs: update installation guide`
- `fix: correct office hours source`
- `feat: add campus map lookup`

一次提交只表达一个清楚的目的。

### 5. 推送并创建 Pull Request

点击 `Publish branch` 或 `Push origin`，然后在 GitHub 创建 Pull Request，目标分支选择 `main`。

PR 描述至少回答三个问题：

1. 为什么要改？
2. 改了什么？
3. 如何确认改动正确？

示例：

```text
为什么：现有安装说明没有明确首次启动步骤。
改了什么：在 docs/guide.md 增加首次启动说明。
如何验证：检查 Markdown 链接，并按说明完成一次本地安装。
```

### 6. 他人评审

PR 至少由一位未参与该改动的成员检查。

- 符合要求：选择 `Approve`。
- 需要修改：选择 `Request changes`，并说明具体文件、问题和期望结果。

作者根据意见在原分支继续修改、提交并推送；PR 会自动更新，不要另开重复 PR。

### 7. 合并与同步

评审通过后，由维护者将 PR 合并到 `main`。初期统一使用 `Create a merge commit`，保留功能提交、评审修订和合并记录。

合并后删除已完成的远端分支。所有成员在开始下一项任务前，回到 `main` 并再次执行 `Fetch origin` 和 `Pull origin`。

## 四条团队规则

1. 不直接向 `main` 推送。
2. 一个任务、一个短分支、一个 PR。
3. Codex 可以修改和检查；人负责确认提交、评审和合并。
4. 看不懂变更时不提交，检查未通过时不合并。
