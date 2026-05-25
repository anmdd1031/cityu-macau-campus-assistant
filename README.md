# 澳门城市大学校园助手 Skill

> 一个让 AI 助手了解澳门城市大学招生、注册、宿舍、签证、学费、课表、数据科学学院学业要求等信息的 Skill。  
> 安装后，你的 AI 助手就能像学长学姐一样回答关于澳城大的常见问题。

## ✨ 功能一览

- 📚 **招生咨询**：内地本科/硕博、本地及国际生报名时间、条件、材料、录取原则
- 💰 **费用查询**：学费、住宿费、保证金范围及退费规则
- 📋 **新生注册**：网络报到、体检、逗留D签注、入境凭条、逗留特别许可全流程
- 🏠 **宿舍与生活**：申请方式、费用、交通攻略、心理咨询、社团
- 🧭 **数据科学学院（FDS）**：课程结构、学分、毕业要求、论文发表、转专业参考、导师联系方式
- 📖 **常用部门**：招生处、教务处、财务部、学生事务处、全球事务处联系方式与位置
- 🌦️ **恶劣天气安排**：台风/黑雨停课规则

> ⚠️ 本 Skill 基于 2026-05-22 公开资料整理。高时效信息（报名时间、费用、宿舍抽签等）请以学校官网最新公告为准。

## 📦 安装方法

### 方法一：Claude Desktop（支持 MCP，体验最佳）

1. 下载本仓库：
   ```bash
   git clone https://github.com/anmdd1031/cityu-macau-campus-assistant.git
2.打开 Claude Desktop → 设置（Settings）→ 开发者（Developer）→ 编辑配置文件（Edit Config）
3.在 mcpServers 中添加以下配置（将路径改为你本地的绝对路径）：
{
  "mcpServers": {
    "cityu-assistant": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-file", "--allowed-directories", "/完整路径/cityu-macau-campus-assistant"]
    }
  }
}
4.重启 Claude Desktop，然后就可以问：“澳门城市大学内地本科什么时候报名？”、“数据科学学院硕士要发论文吗？”等。

###方法二：Cursor / Windsurf / VS Code（支持 MCP 的编辑器）

Cursor / Windsurf：原生支持 MCP，在设置中添加上述配置即可。
VS Code：安装 Continue 或 Cline 插件，然后在插件配置中导入 MCP Server。

###方法三：任何 AI 聊天工具（通用方法）
直接复制 knowledge-base/freshman.md 和 knowledge-base/fds.md 的内容（可合并），粘贴到系统提示词（System Prompt）或自定义指令框中。例如：

DeepSeek

Kimi

智谱清言

豆包

GitHub Copilot Chat

💡 多文件说明：本 Skill 将通用知识（freshman.md）和学院知识（fds.md）分开存放。如果你的 Agent 支持读取整个文件夹（如 Claude Desktop + MCP file server），直接按方法一配置即可。如果只接受单个文件，请手动合并两个 md 文件的内容后导入。
