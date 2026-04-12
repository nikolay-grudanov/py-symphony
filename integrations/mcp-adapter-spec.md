# MCP (Model Context Protocol) Adapter Specification

**Статус**: Draft | **Версия**: 0.1

## Назначение и область применения

Данный документ определяет спецификацию интеграции с MCP (Model Context Protocol) для Symphony сервиса.

**Цель**:
- Обеспечить интеграцию MCP tools и resources с agent protocol
- Поддержать динамическое обнаружение и регистрацию MCP tools
- Обеспечить прозрачное взаимодействие между agents и MCP servers

**Область применения**:
- Обнаружение MCP servers и их capabilities
- Регистрация MCP tools в agent runtime
- Выполнение MCP tool calls
- Управление MCP resources
- Обработка ошибок MCP protocol

## MCP Overview

### Что такое MCP?
Model Context Protocol (MCP) - открытый протокол для интеграции external tools и resources с LLM agents.

**Ключевые понятия**:
- **MCP Server**: сервис, предоставляющий tools и resources
- **MCP Tool**: callable функция, доступная agent
- **MCP Resource**: статический или динамический ресурс (файлы, данные, etc.)
- **MCP Client**: компонент, взаимодействующий с MCP server

**Больше информации**: https://modelcontextprotocol.io

## Архитектура интеграции

### Компоненты
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Orchestrator  │────▶│ Agent Runner    │────▶│  MCP Adapter    │
│                 │     │  - Session      │     │  - Discovery    │
│  - Issue State  │     │  - Tool Calls   │     │  - Registry     │
│  - Workflows    │     │  - Streaming    │     │  - Execution    │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                      │
                                 │                      ▼
                                 │              ┌─────────────────┐
                                 │              │ MCP Servers     │
                                 │              │  - Filesystem   │
                                 │              │  - Database     │
                                 │              │  - HTTP         │
                                 │              │  - Custom       │
                                 │              └─────────────────┘
                                 │
                                 ▼
                         ┌─────────────────┐
                         │ Codex App-Server│
                         │  - Tools API    │
                         │  - Events       │
                         └─────────────────┘
```

### Интеграция с Agent Protocol
MCP adapter интегрируется с Codex app-server protocol (см. SPEC.md Section 10):

1. **Discovery Phase**: Находятся доступные MCP servers
2. **Registration Phase**: MCP tools регистрируются в app-server
3. **Execution Phase**: Tool calls выполняются через MCP adapter
4. **Streaming Phase**: Результаты стримятся обратно в orchestrator

## MCP Tools and Resources

### MCP Tools Schema
MCP tool определение:
```json
{
  "name": "tool_name",
  "description": "Tool description",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param1"]
  }
}
```

### MCP Resources Schema
MCP resource определение:
```json
{
  "uri": "resource://server/resource_id",
  "name": "Resource name",
  "description": "Resource description",
  "mimeType": "text/plain",
  "metadata": {
    "custom": "metadata"
  }
}
```

## Интеграция с Agent Protocol

### Tool Discovery

#### Phase 1: MCP Server Discovery
**Назначение**: Обнаружение доступных MCP servers

**Методы обнаружения**:
- Configuration-based: MCP servers указаны в WORKFLOW.md
- Dynamic discovery: mDNS/DNS-SD based discovery
- Environment-based: MCP servers из environment variables

**Конфигурация в WORKFLOW.md**:
```yaml
mcp:
  enabled: true
  servers:
    - name: "filesystem"
      type: "filesystem"
      config:
        root_path: "/data"
    - name: "database"
      type: "database"
      config:
        connection_string: "$DB_CONNECTION"
    - name: "http"
      type: "http"
      config:
        endpoint: "https://api.example.com/mcp"
```

**Возвращает**: Список доступных MCP servers

#### Phase 2: Tool Listing
**Назначение**: Получение списка tools от каждого MCP server

**Операция**:
```
GET /tools (MCP protocol)
```

**Возвращает**: Список tool definitions

### Tool Registration

#### Регистрация в Codex App-Server
**Назначение**: Регистрация MCP tools в app-server runtime

**Интеграция с SPEC.md Section 10.2**:

В phase `thread/start` или `initialized`, MCP adapter advertises MCP tools:

```json
{
  "id": 4,
  "method": "tools/register",
  "params": {
    "tools": [
      {
        "name": "mcp_filesystem_read",
        "description": "Read file from MCP filesystem server",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": {
              "type": "string",
              "description": "File path to read"
            }
          },
          "required": ["path"]
        }
      }
    ]
  }
}
```

**Детали реализации**:
- MCP tools регистрируются с префиксом `mcp_`
- Интеграция с optional client-side tool extension (SPEC.md Section 10.5)
- Динамическая регистрация при добавлении новых MCP servers

### Tool Execution

#### Обработка Tool Calls
**Назначение**: Выполнение MCP tool calls от agent

**Поток выполнения**:
```
1. Agent вызывает tool (например: mcp_filesystem_read)
2. App-Server отправляет tool call event
3. MCP Adapter перехватывает call
4. MCP Adapter форвардит call в MCP server
5. MCP Server возвращает результат
6. MCP Adapter форвардит результат в App-Server
7. App-Server отправляет tool result в agent
```

**Пример события tool call**:
```json
{
  "event": "item/tool/call",
  "params": {
    "tool": "mcp_filesystem_read",
    "input": {
      "path": "/data/file.txt"
    },
    "callId": "call_123"
  }
}
```

**Пример ответа**:
```json
{
  "id": "call_123",
  "result": {
    "success": true,
    "output": {
      "type": "text",
      "text": "File contents..."
    }
  }
}
```

**Ошибка выполнения**:
```json
{
  "id": "call_123",
  "result": {
    "success": false,
    "error": "File not found"
  }
}
```

## MCP Tool Discovery and Registration

### Автоматическое обнаружение

#### 1. Configuration Discovery
**Назначение**: Обнаружение MCP servers из конфигурации

**Источники конфигурации**:
- WORKFLOW.md front matter
- Environment variables
- Configuration files

**Пример**:
```yaml
mcp:
  discovery:
    method: "config"
    sources:
      - "workflow"
      - "env"
      - "./mcp-servers.yaml"
```

#### 2. Service Discovery (mDNS/DNS-SD)
**Назначение**: Обнаружение MCP servers в сети

**Детали реализации**:
- Использует mDNS для обнаружения локальных MCP servers
- DNS-SD для обнаружения в larger networks
- Опциональная фильтрация по типу/namespace

**Пример**:
```yaml
mcp:
  discovery:
    method: "mdns"
    filters:
      - service_type: "_mcp._tcp"
      - namespace: "symphony"
```

### Tool Registry

#### Registry Schema
```json
{
  "tools": {
    "mcp_filesystem_read": {
      "name": "mcp_filesystem_read",
      "server": "filesystem",
      "description": "Read file from MCP filesystem server",
      "inputSchema": { /* ... */ },
      "registered_at": "2024-01-01T00:00:00Z",
      "enabled": true
    },
    "mcp_database_query": {
      "name": "mcp_database_query",
      "server": "database",
      "description": "Query MCP database server",
      "inputSchema": { /* ... */ },
      "registered_at": "2024-01-01T00:00:00Z",
      "enabled": true
    }
  },
  "servers": {
    "filesystem": {
      "name": "filesystem",
      "type": "filesystem",
      "status": "connected",
      "tools": ["mcp_filesystem_read", "mcp_filesystem_write"]
    },
    "database": {
      "name": "database",
      "type": "database",
      "status": "connected",
      "tools": ["mcp_database_query"]
    }
  }
}
```

#### Registry Operations
- `register_tool(tool_definition)` - регистрация tool
- `unregister_tool(tool_name)` - удаление tool
- `get_tool(tool_name)` - получение tool definition
- `list_tools(server_name)` - список tools для server
- `list_servers()` - список MCP servers
- `enable_tool(tool_name)` - включение tool
- `disable_tool(tool_name)` - отключение tool

## Resource Management

### Resource Listing
**Назначение**: Получение списка available resources

**Операция**:
```
GET /resources (MCP protocol)
```

**Возвращает**: Список resource definitions

### Resource Reading
**Назначение**: Чтение содержимого resource

**Операция**:
```
GET /resources/{uri} (MCP protocol)
```

**Возвращает**: Resource content

### Resource Subscription
**Назначение**: Подписка на изменения resource (для dynamic resources)

**Операция**:
```
POST /resources/subscribe (MCP protocol)
```

**Возвращает**: Subscription ID

**Streaming updates**:
```json
{
  "event": "resource_updated",
  "subscription_id": "sub_123",
  "uri": "resource://server/resource_id",
  "content": "Updated content..."
}
```

## Обработка ошибок

### Категории ошибок MCP Protocol

| Категория | Описание | Обработка |
|-----------|-----------|-----------|
| `mcp_server_not_found` | MCP server не найден | Fatal error |
| `mcp_connection_error` | Ошибка подключения к server | Retry с backoff |
| `mcp_tool_not_found` | Tool не найден в registry | Return error to agent |
| `mcp_tool_execution_error` | Ошибка выполнения tool | Return error to agent |
| `mcp_invalid_input` | Неверный ввод для tool | Return validation error |
| `mcp_resource_not_found` | Resource не найден | Return error to agent |
| `mcp_auth_error` | Ошибка аутентификации | Fatal error |
| `mcp_timeout` | Превышен timeout | Return timeout error |

### Retry политика
- Connection errors: retry с exponential backoff (max 5 attempts)
- Tool execution errors: немедленный return ошибки
- Timeout errors: немедленный return timeout
- Auth errors: немедленный fatal

## Конфигурация

### WORKFLOW.md front matter
```yaml
mcp:
  enabled: true

  discovery:
    method: "config"
    auto_discover: true
    refresh_interval_ms: 300000

  servers:
    - name: "filesystem"
      type: "filesystem"
      enabled: true
      config:
        root_path: "/data"
        read_only: false

    - name: "database"
      type: "database"
      enabled: true
      config:
        connection_string: "$DB_CONNECTION"
        pool_size: 10

    - name: "http"
      type: "http"
      enabled: true
      config:
        endpoint: "https://api.example.com/mcp"
        timeout_ms: 30000

  tool_registration:
    prefix: "mcp_"
    auto_register: true
    validate_schema: true

  execution:
    timeout_ms: 60000
    max_concurrent_calls: 10
```

## Безопасность

### Инварианты безопасности
1. **Tool Sandboxing**: MCP tools выполняются в изолированном контексте
2. **Input Validation**: Все inputs валидируются по schema перед выполнением
3. **Resource Access Control**: Доступ к resources регулируется ACL
4. **Credential Protection**: Никогда не логировать credentials MCP servers

### Рекомендации
- Использовать read-only MCP servers когда возможно
- Валидировать inputs от agents перед форвардингом в MCP servers
- Мониторировать MCP tool usage для аномалий
- Использовать rate limiting для MCP tool calls

## Observability

### Logging
- MCP server discovery events
- Tool registration/unregistration
- Tool execution (success/failure)
- Resource access
- Error handling

### Metrics
- MCP tool call count (by tool name)
- MCP tool execution latency
- MCP server connection status
- Resource access count

### Tracing
- Distributed tracing для tool calls через MCP adapter
- Trace spans для MCP server communication

## TODO

### Определить MCP Tool Registry
- **Задача**: Определить детальную спецификацию MCP tool registry
- **Детали**:
  - Schema для tool definitions
  - API для CRUD операций над registry
  - Persistence layer для registry
  - Versioning для tool definitions
  - Migration strategy для registry updates

### Дополнительные задачи
- [ ] Определить формат для MCP server health checks
- [ ] Реализовать поддержку MCP tool batching
- [ ] Добавить поддержку MCP tool streaming responses
- [ ] Определить стратегию для MCP tool caching
- [ ] Реализовать support для MCP tool ACL
- [ ] Реализовать unit tests для MCP adapter
- [ ] Добавить интеграционные тесты с real MCP servers
- [ ] Определить ограничения на concurrent MCP tool calls
- [ ] Поддержать MCP server hot-reload
- [ ] Добавить поддержку MCP tool deprecation warnings
- [ ] Определить стратегию для MCP server failover
- [ ] Реализовать support для MCP tool timeouts per server
- [ ] Добавить поддержку MCP tool telemetry

## Ссылки

- SPEC.md: Symphony Service Specification
- SPEC.md Section 10: Agent Runner Protocol (Coding Agent Integration)
- SPEC.md Section 10.5: Optional Client-side Tool Extension
- Model Context Protocol: https://modelcontextprotocol.io
- MCP Specification: https://spec.modelcontextprotocol.io
