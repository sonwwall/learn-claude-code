# MCP Ecommerce Server

为 Claude 提供电商数据查询能力的 MCP 服务器。

## 功能特性

### 🛠️ 工具 (Tools)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `query_order` | 查询订单详情 | `order_id`: 订单号 |
| `check_inventory` | 查询商品库存 | `sku_or_name`: SKU或名称 |
| `get_sales_stats` | 销售统计 | `days`: 统计天数(默认30) |
| `search_orders` | 搜索订单 | `customer_name`, `status`, `date_from`, `date_to` |
| `get_low_stock_items` | 低库存预警 | `threshold`: 库存阈值(默认10) |

### 📚 资源 (Resources)

| 资源 URI | 描述 |
|----------|------|
| `config://ecommerce-settings` | 商城配置信息 |
| `logs://recent-orders` | 最近订单日志 |

## 安装

### 1. 安装依赖

```bash
cd mcp-ecommerce-server
python3 -m venv venv
source venv/bin/activate
pip install mcp
```

### 2. 配置 Claude

编辑 `~/.claude/mcp.json`：

```json
{
  "mcpServers": {
    "ecommerce": {
      "command": "python3",
      "args": ["/Users/ruitong/vscode/learn-claude-code/mcp-ecommerce-server/server.py"]
    }
  }
}
```

### 3. 重启 Claude

Claude 会自动发现并连接到这个 MCP 服务器。

## 使用示例

配置完成后，你可以在 Claude 中这样使用：

```
用户: 查询订单 ORD-2024-001
Claude: [调用 query_order 工具]

用户: 智能手机 Pro 有货吗
Claude: [调用 check_inventory 工具]

用户: 最近销售情况怎么样
Claude: [调用 get_sales_stats 工具]

用户: 有哪些订单待发货
Claude: [调用 search_orders 工具，status="待发货"]

用户: 哪些商品库存不足
Claude: [调用 get_low_stock_items 工具]
```

## 测试

使用 MCP Inspector 测试：

```bash
npx @anthropics/mcp-inspector python3 server.py
```

或直接测试：

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 server.py
```

## 扩展

你可以轻松扩展这个服务器：

1. **添加新工具**：复制 `@server.tool()` 装饰的函数
2. **连接真实数据库**：替换 `ORDERS_DB` 和 `INVENTORY_DB`
3. **添加认证**：在工具函数中添加权限检查
4. **添加资源**：使用 `@server.resource()` 暴露更多数据

## 架构

```
Claude ←→ MCP Protocol ←→ Ecommerce Server ←→ Database/API
              ↑
         Tools: query_order, check_inventory...
         Resources: config, logs...
```
