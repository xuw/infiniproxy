# OpenAI 到 Claude API 代理服务器

一个本地代理服务器，用于在 OpenAI 兼容的 API 格式和 Claude（Anthropic）API 格式之间进行转换，允许 Claude Code 和其他基于 Claude 的工具使用 OpenAI 兼容的后端。

## 功能特性

- ✅ **双重 API 支持**：同时支持 Claude API 格式和 OpenAI API 格式
- ✅ **转换模式**：Claude API 请求 → OpenAI 后端（带格式转换）
- ✅ **透传模式**：OpenAI API 请求 → OpenAI 后端（无转换）
- ✅ **多用户支持**：支持多个用户的 API 密钥认证
- ✅ **使用量跟踪**：跟踪每个 API 密钥的令牌使用量
- ✅ **管理端点**：用户和 API 密钥管理
- ✅ **基于 Web 的管理界面**：用于管理用户和查看使用情况的精美界面
- ✅ 正确处理系统消息
- ✅ 支持多轮对话
- ✅ 处理 Claude 的内容块
- ✅ **完整的工具/函数调用支持**
- ✅ 推理模型的特殊支持（如 glm-4.6）
- ✅ 全面的测试套件
- ✅ 通过环境变量轻松配置

## 架构

代理支持两种模式：

### 转换模式（Claude API → OpenAI 后端）
```
Claude Code → HTTP (Claude 格式) → 代理服务器 → HTTP (OpenAI 格式) → OpenAI 兼容后端
                                      /v1/messages
                                           ↓ (转换)
Claude Code ← HTTP (Claude 格式) ← 代理服务器 ← HTTP (OpenAI 格式) ← OpenAI 兼容后端
```

### 透传模式（OpenAI API → OpenAI 后端）
```
OpenAI 客户端 → HTTP (OpenAI 格式) → 代理服务器 → HTTP (OpenAI 格式) → OpenAI 兼容后端
                                        /v1/chat/completions
                                             ↓ (透传)
OpenAI 客户端 ← HTTP (OpenAI 格式) ← 代理服务器 ← HTTP (OpenAI 格式) ← OpenAI 兼容后端
```

## 安装

1. 克隆或下载此仓库
2. 创建虚拟环境并安装依赖：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. 配置环境变量：

```bash
# 复制示例 .env 文件
cp .env.example .env

# 编辑 .env 文件设置你的配置
nano .env
```

## 配置

编辑 `.env` 文件设置你的配置：

```bash
# OpenAI 兼容后端配置
OPENAI_BASE_URL=https://cloud.infini-ai.com/maas/v1/chat/completions
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=glm-4.6

# 代理服务器配置
PROXY_HOST=localhost
PROXY_PORT=8000

# 可选设置
TIMEOUT=300
DEBUG=false
```

## 使用方法

### 启动代理服务器

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行代理服务器
python proxy_server.py
```

服务器将在 `http://localhost:8000`（或你配置的端口）启动。

### 基于 Web 的管理界面

管理用户和 API 密钥的最简单方式是通过基于 Web 的管理界面：

**访问管理界面：**
```
http://localhost:8000/admin
```

管理界面提供：
- 👥 **用户选项卡**：创建和查看所有用户
- 🔑 **API 密钥选项卡**：生成、查看和停用 API 密钥
- 📊 **使用统计选项卡**：查看每个 API 密钥的令牌使用情况

**功能特性：**
- 精美、响应式界面
- 实时数据更新
- 安全的 API 密钥生成（仅显示一次）
- 使用情况跟踪可视化
- 按用户过滤 API 密钥
- 一键停用密钥

### 命令行用户和 API 密钥管理

你也可以通过命令行管理用户和密钥：

在使用代理之前，你需要创建用户和 API 密钥：

**1. 创建用户：**
```bash
curl -X POST "http://localhost:8000/admin/users?username=alice&email=alice@example.com"
```

响应：
```json
{
  "success": true,
  "user_id": 1,
  "username": "alice",
  "message": "用户 alice 创建成功"
}
```

**2. 为用户创建 API 密钥：**
```bash
curl -X POST "http://localhost:8000/admin/api-keys?user_id=1&name=my-key"
```

响应：
```json
{
  "success": true,
  "api_key": "sk-abc123...",
  "user_id": 1,
  "name": "my-key",
  "warning": "保存此 API 密钥！它将不会再次显示。"
}
```

**重要提示：** 立即保存 API 密钥 - 稍后无法检索！

**3. 列出所有用户：**
```bash
curl http://localhost:8000/admin/users
```

**4. 列出 API 密钥：**
```bash
curl http://localhost:8000/admin/api-keys
# 或者特定用户的：
curl "http://localhost:8000/admin/api-keys?user_id=1"
```

**5. 停用 API 密钥：**
```bash
curl -X DELETE http://localhost:8000/admin/api-keys/1
```

### 与 Claude Code 一起使用

配置 Claude Code 将代理作为其 API 端点：

1. 将 API 端点设置为：`http://localhost:8000`
2. 将 API 密钥设置为你生成的密钥（来自上面的 API 密钥创建步骤）
3. 代理在 `/v1/messages` 接受 Claude API 格式

### 与 OpenAI 兼容的客户端一起使用

你可以将代理与任何 OpenAI 兼容的客户端或库一起使用：

**Python (OpenAI SDK)：**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-abc123..."  # 来自密钥创建步骤的 API 密钥
)

response = client.chat.completions.create(
    model="glm-4.6",
    messages=[
        {"role": "user", "content": "你好！"}
    ]
)
```

**JavaScript/TypeScript (OpenAI SDK)：**
```javascript
import OpenAI from 'openai';

const client = new OpenAI({
    baseURL: 'http://localhost:8000/v1',
    apiKey: 'sk-abc123...'  // 你的 API 密钥
});

const response = await client.chat.completions.create({
    model: 'glm-4.6',
    messages: [{ role: 'user', content: '你好！' }]
});
```

**cURL：**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-abc123..." \
  -d '{
    "model": "glm-4.6",
    "messages": [{"role": "user", "content": "你好！"}]
  }'
```

### API 端点

#### `GET /`
返回服务器信息和可用端点。

```bash
curl http://localhost:8000/
```

#### `GET /health`
健康检查端点。

```bash
curl http://localhost:8000/health
```

#### `POST /v1/messages`
Claude API 端点（转换为 OpenAI 格式）。

此端点接受 Claude API 格式请求，将其转换为 OpenAI 格式，
并以 Claude 格式返回响应。

**需要通过 Bearer 令牌进行身份验证。**

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-abc123..." \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "你好！"
      }
    ]
  }'
```

#### `POST /v1/chat/completions`
OpenAI API 端点（透传模式）。

此端点接受 OpenAI API 格式请求并直接传递给后端而不进行转换，
返回 OpenAI 格式的响应。

**需要通过 Bearer 令牌进行身份验证。**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-abc123..." \
  -d '{
    "model": "glm-4.6",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "你好！"
      }
    ]
  }'
```

### 使用量跟踪端点

#### `GET /usage/me`
获取经过身份验证的用户的使用统计信息。

```bash
curl http://localhost:8000/usage/me \
  -H "Authorization: Bearer sk-abc123..."

# 带日期范围：
curl "http://localhost:8000/usage/me?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59" \
  -H "Authorization: Bearer sk-abc123..."
```

响应：
```json
{
  "user_id": 1,
  "username": "alice",
  "total_requests": 42,
  "total_input_tokens": 1500,
  "total_output_tokens": 3000,
  "total_tokens": 4500,
  "usage_by_endpoint": [
    {
      "endpoint": "/v1/chat/completions",
      "model": "glm-4.6",
      "total_requests": 25,
      "total_input_tokens": 900,
      "total_output_tokens": 1800,
      "total_tokens": 2700
    }
  ]
}
```

### 管理端点

#### `POST /admin/users`
创建新用户（如上用户管理部分所示）。

#### `POST /admin/api-keys`
为用户创建 API 密钥（如上用户管理部分所示）。

#### `GET /admin/users`
列出所有用户。

#### `GET /admin/api-keys`
列出所有 API 密钥或特定用户的密钥。

#### `DELETE /admin/api-keys/{api_key_id}`
停用 API 密钥。

#### `GET /usage/api-key/{api_key_id}`
获取特定 API 密钥的使用统计信息。

## 测试

### 单元测试

运行全面的测试套件：

```bash
source venv/bin/activate
pytest tests/ -v
```

### 端到端测试

使用真实 API 调用测试代理：

```bash
# 首先确保代理服务器正在运行
python proxy_server.py

# 在另一个终端中：
source venv/bin/activate
python test_e2e.py
```

### 手动测试

你也可以使用测试脚本来验证 OpenAI 端点是否工作：

```bash
source venv/bin/activate
python test_api.py
```

## API 转换详情

### 请求转换（Claude → OpenAI）

代理将 Claude API 请求转换为 OpenAI 格式：

- **系统消息**：从 `system` 字段提取并添加为第一个 `role: "system"` 的消息
- **内容块**：Claude 的内容块（例如 `[{"type": "text", "text": "..."}]`）被转换为简单字符串
- **参数**：`max_tokens`、`temperature`、`top_p`、`stop_sequences` 被适当映射

### 响应转换（OpenAI → Claude）

OpenAI 响应被转换回 Claude 格式：

- **消息结构**：包装在 Claude 的内容块格式中
- **停止原因**：从 OpenAI 的 `finish_reason` 映射到 Claude 的 `stop_reason`
  - `stop` → `end_turn`
  - `length` → `max_tokens`
  - `content_filter` → `content_filtered`
- **使用量令牌**：从 `prompt_tokens`/`completion_tokens` 映射到 `input_tokens`/`output_tokens`
- **推理内容**：对具有 `reasoning_content` 的模型的特殊处理（如 glm-4.6）

## 项目结构

```
infiniproxy/
├── config.py              # 配置管理
├── translator.py          # 请求/响应转换逻辑
├── openai_client.py       # OpenAI API 客户端
├── user_manager.py        # 用户和 API 密钥管理
├── proxy_server.py        # 主代理服务器 (FastAPI)
├── proxy_users.db         # SQLite 数据库（不在 git 中）
├── requirements.txt       # Python 依赖
├── .env                   # 配置（不在 git 中）
├── .gitignore            # Git 忽略模式
├── DESIGN.md             # 架构和设计文档
├── README.md             # 英文文档
├── README-cn.md          # 中文文档（本文件）
├── test_api.py           # API 验证脚本
├── test_e2e.py           # 端到端测试
├── static/               # 管理界面资源
│   ├── admin.html        # 管理界面 HTML
│   └── admin.js          # 管理界面 JavaScript
└── tests/                # 单元测试
    ├── __init__.py
    ├── test_translator.py
    └── test_proxy_server.py
```

## 限制

- **流式传输**：目前未完全实现。流式请求回退到非流式响应。
- **图像**：转换中尚不支持图像内容块。

## 故障排除

### 连接被拒绝
- 确保代理服务器正在运行
- 检查端口（默认 8000）未被其他应用程序使用
- 验证防火墙设置允许到 localhost 的连接

### API 密钥错误
- 验证 `.env` 文件中的 `OPENAI_API_KEY` 是否正确
- 检查 OpenAI 兼容端点是否可访问

### 转换错误
- 通过在 `.env` 中设置 `DEBUG=true` 启用调试日志
- 检查服务器日志以获取详细错误消息
- 验证请求格式是否符合 Claude API 规范

### 测试失败
- 确保所有依赖已安装：`pip install -r requirements.txt`
- 对于端到端测试，确保代理服务器正在运行
- 检查 OpenAI 后端端点是否可访问

## 开发

### 在开发模式下运行

```bash
# 启用调试日志
export DEBUG=true

# 使用自动重新加载运行
uvicorn proxy_server:app --reload --host localhost --port 8000
```

### 添加新功能

1. 更新 `translator.py` 进行转换逻辑更改
2. 更新 `openai_client.py` 进行客户端更改
3. 在 `tests/` 目录中添加测试
4. 更新文档

## 许可证

本项目按原样提供，用于教育和开发目的。

## 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建功能分支
3. 为新功能添加测试
4. 确保所有测试通过
5. 提交 Pull Request

## 支持

如有问题或疑问：

1. 检查故障排除部分
2. 查看 DESIGN.md 了解架构详情
3. 在仓库上打开 issue