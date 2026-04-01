#!/usr/bin/env python3
"""
MCP Ecommerce Server

为 Claude 提供电商数据查询能力的 MCP 服务器。
"""

import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 创建 MCP 服务器实例
app = Server("ecommerce-server")

# ============ 模拟电商数据库 ============

ORDERS_DB = {
    "ORD-2024-001": {
        "customer_name": "张三",
        "items": [{"sku": "PHONE-001", "name": "智能手机 Pro", "qty": 1, "price": 4999}],
        "status": "已发货",
        "order_date": "2024-03-15",
        "total": 4999
    },
    "ORD-2024-002": {
        "customer_name": "李四",
        "items": [
            {"sku": "LAPTOP-001", "name": "超薄笔记本", "qty": 1, "price": 8999},
            {"sku": "MOUSE-001", "name": "无线鼠标", "qty": 1, "price": 199}
        ],
        "status": "待发货",
        "order_date": "2024-03-20",
        "total": 9198
    }
}

INVENTORY_DB = {
    "PHONE-001": {"name": "智能手机 Pro", "stock": 50, "price": 4999},
    "LAPTOP-001": {"name": "超薄笔记本", "stock": 20, "price": 8999},
    "MOUSE-001": {"name": "无线鼠标", "stock": 200, "price": 199}
}

# ============ 工具处理函数 ============

async def handle_query_order(order_id: str) -> str:
    if order_id not in ORDERS_DB:
        return f"❌ 未找到订单 {order_id}"

    order = ORDERS_DB[order_id]
    items_str = "\n".join([
        f"  • {item['name']} × {item['qty']} = ¥{item['price'] * item['qty']}"
        for item in order["items"]
    ])

    return f"""📦 订单详情
订单号: {order_id}
客户: {order['customer_name']}
状态: {order['status']}
日期: {order['order_date']}

商品:
{items_str}

总额: ¥{order['total']}"""

async def handle_check_inventory(sku: str) -> str:
    if sku not in INVENTORY_DB:
        return f"❌ 未找到商品 {sku}"

    item = INVENTORY_DB[sku]
    status = "✅ 有货" if item["stock"] > 0 else "❌ 缺货"

    return f"""📱 商品信息
名称: {item['name']}
SKU: {sku}
价格: ¥{item['price']}
库存: {item['stock']} 件
状态: {status}"""

# ============ MCP 处理器 ============

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_order",
            description="查询订单详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号"}
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="check_inventory",
            description="查询商品库存",
            inputSchema={
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "商品SKU"}
                },
                "required": ["sku"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_order":
        result = await handle_query_order(arguments["order_id"])
    elif name == "check_inventory":
        result = await handle_check_inventory(arguments["sku"])
    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=result)]

# ============ 运行服务器 ============

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
