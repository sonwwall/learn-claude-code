#!/usr/bin/env python3
"""
ecommerce_support_agent.py - 电商客服代理

一个专业的电商客服AI代理，能够处理订单查询、库存检查、退货处理等常见客服任务。

核心理念：模型本身就是代理，代码只是提供能力。
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

# 初始化Anthropic客户端
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url=os.getenv("ANTHROPIC_BASE_URL")
)
MODEL = os.environ.get("MODEL_ID", "claude-3-sonnet-20240229")

# ============ 模拟数据库 ============
# 在实际生产环境中，这些应该连接到真实的订单系统、库存系统等

ORDERS_DB = {
    "ORD-2024-001": {
        "customer_id": "CUST-001",
        "customer_name": "张三",
        "items": [
            {"sku": "PHONE-001", "name": "智能手机 Pro", "qty": 1, "price": 4999}
        ],
        "status": "已发货",
        "order_date": "2024-03-15",
        "shipping_date": "2024-03-16",
        "tracking_number": "SF1234567890",
        "address": "北京市朝阳区xxx街道xxx号"
    },
    "ORD-2024-002": {
        "customer_id": "CUST-002",
        "customer_name": "李四",
        "items": [
            {"sku": "LAPTOP-001", "name": "超薄笔记本", "qty": 1, "price": 8999},
            {"sku": "MOUSE-001", "name": "无线鼠标", "qty": 1, "price": 199}
        ],
        "status": "待发货",
        "order_date": "2024-03-20",
        "shipping_date": None,
        "tracking_number": None,
        "address": "上海市浦东新区xxx路xxx号"
    },
    "ORD-2024-003": {
        "customer_id": "CUST-001",
        "customer_name": "张三",
        "items": [
            {"sku": "HEADPHONE-001", "name": "降噪耳机", "qty": 1, "price": 1299}
        ],
        "status": "已完成",
        "order_date": "2024-02-10",
        "shipping_date": "2024-02-11",
        "tracking_number": "SF0987654321",
        "address": "北京市朝阳区xxx街道xxx号"
    }
}

INVENTORY_DB = {
    "PHONE-001": {"name": "智能手机 Pro", "stock": 50, "price": 4999, "category": "手机"},
    "LAPTOP-001": {"name": "超薄笔记本", "stock": 20, "price": 8999, "category": "电脑"},
    "MOUSE-001": {"name": "无线鼠标", "stock": 200, "price": 199, "category": "配件"},
    "HEADPHONE-001": {"name": "降噪耳机", "stock": 0, "price": 1299, "category": "配件"},
    "TABLET-001": {"name": "平板电脑 Air", "stock": 30, "price": 3999, "category": "平板"}
}

RETURNS_DB = {}  # 退货记录

# ============ 客服知识库 ============

SUPPORT_KNOWLEDGE = """
## 退换货政策
- 7天无理由退货：自签收之日起7天内，商品未使用、包装完好可申请退货
- 质量问题退货：15天内发现质量问题，可免费退货并承担运费
- 换货政策：30天内可申请换货，需保证商品完好

## 配送时效
- 标准快递：3-5个工作日
- 顺丰快递：1-3个工作日
- 偏远地区：可能延长2-3天

## 售后服务时间
- 在线客服：9:00-22:00
- 电话客服：9:00-18:00

## 常见问题
Q: 如何查询订单物流？
A: 提供订单号即可查询物流状态和快递单号

Q: 商品缺货怎么办？
A: 可以设置到货提醒，或选择类似商品推荐

Q: 如何申请退货？
A: 提供订单号和退货原因，客服会协助处理
"""

# ============ 系统提示词 ============

SYSTEM_PROMPT = f"""你是专业的电商客服AI助手，致力于为客户提供优质的服务体验。

## 你的职责
1. 友好、耐心地解答客户问题
2. 准确查询订单、库存信息
3. 协助处理退货、换货申请
4. 必要时将复杂问题升级给人工客服

## 服务原则
- 始终以客户为中心，语气温和礼貌
- 回答要准确、清晰、有帮助
- 不确定的问题不要猜测，主动升级
- 保护客户隐私，不泄露敏感信息

## 可用工具
你可以使用以下工具来帮助客户：
- query_order: 查询订单状态和详情
- check_inventory: 查询商品库存和价格
- process_return: 处理退货申请
- send_message: 给客户发送通知或消息
- escalate: 将问题升级给人工客服

## 客服知识
{SUPPORT_KNOWLEDGE}

## 当前时间
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

# ============ 工具函数 ============

def query_order(order_id: str) -> str:
    """查询订单状态和详情"""
    if order_id not in ORDERS_DB:
        return f"未找到订单 {order_id}，请检查订单号是否正确。"
    
    order = ORDERS_DB[order_id]
    items_str = "\n".join([
        f"  - {item['name']} (SKU: {item['sku']}) x{item['qty']} = ¥{item['price'] * item['qty']}"
        for item in order["items"]
    ])
    
    total = sum(item["price"] * item["qty"] for item in order["items"])
    
    result = f"""订单号: {order_id}
客户: {order['customer_name']}
下单日期: {order['order_date']}
订单状态: {order['status']}
收货地址: {order['address']}

商品明细:
{items_str}

订单总额: ¥{total}"""
    
    if order["shipping_date"]:
        result += f"\n发货日期: {order['shipping_date']}"
    if order["tracking_number"]:
        result += f"\n快递单号: {order['tracking_number']}"
    
    return result


def check_inventory(sku_or_name: str) -> str:
    """查询商品库存和价格"""
    # 先尝试精确匹配SKU
    if sku_or_name in INVENTORY_DB:
        item = INVENTORY_DB[sku_or_name]
        stock_status = "有货" if item["stock"] > 0 else "暂时缺货"
        return f"""商品: {item['name']}
SKU: {sku_or_name}
价格: ¥{item['price']}
库存: {item['stock']} 件
状态: {stock_status}
分类: {item['category']}"""
    
    # 尝试模糊匹配商品名称
    matches = []
    for sku, item in INVENTORY_DB.items():
        if sku_or_name.lower() in item['name'].lower():
            matches.append((sku, item))
    
    if len(matches) == 1:
        sku, item = matches[0]
        stock_status = "有货" if item["stock"] > 0 else "暂时缺货"
        return f"""商品: {item['name']}
SKU: {sku}
价格: ¥{item['price']}
库存: {item['stock']} 件
状态: {stock_status}
分类: {item['category']}"""
    
    elif len(matches) > 1:
        result = "找到多个匹配商品:\n"
        for sku, item in matches:
            stock_status = "有货" if item["stock"] > 0 else "缺货"
            result += f"- {item['name']} (SKU: {sku}) ¥{item['price']} [{stock_status}]\n"
        return result
    
    return f"未找到商品 '{sku_or_name}'，请检查SKU或商品名称。"


def process_return(order_id: str, reason: str, items: Optional[List[str]] = None) -> str:
    """处理退货申请"""
    if order_id not in ORDERS_DB:
        return f"未找到订单 {order_id}，无法处理退货。"
    
    order = ORDERS_DB[order_id]
    
    # 检查订单状态是否允许退货
    if order["status"] not in ["已完成", "已发货"]:
        return f"订单状态为 '{order['status']}'，暂不符合退货条件。"
    
    # 生成退货单号
    return_id = f"RET-{order_id}-{datetime.now().strftime('%Y%m%d')}"
    
    # 记录退货
    RETURNS_DB[return_id] = {
        "order_id": order_id,
        "customer_name": order["customer_name"],
        "reason": reason,
        "items": items or [item["name"] for item in order["items"]],
        "status": "待审核",
        "apply_date": datetime.now().strftime("%Y-%m-%d"),
        "refund_amount": sum(item["price"] * item["qty"] for item in order["items"])
    }
    
    return f"""退货申请已提交！
退货单号: {return_id}
订单号: {order_id}
退货原因: {reason}
退款金额: ¥{RETURNS_DB[return_id]['refund_amount']}

我们的售后团队会在1-2个工作日内审核您的申请，请保持手机畅通。"""


def send_message(customer_id: str, message: str, channel: str = "app") -> str:
    """给客户发送消息或通知"""
    channels = {
        "app": "APP推送",
        "sms": "短信",
        "email": "邮件"
    }
    
    channel_name = channels.get(channel, "APP推送")
    
    # 模拟发送
    return f"消息已通过{channel_name}发送给客户 {customer_id}:\n{message}"


def escalate(reason: str, priority: str = "normal") -> str:
    """将问题升级给人工客服"""
    priorities = {
        "low": "低优先级",
        "normal": "普通优先级",
        "high": "高优先级",
        "urgent": "紧急"
    }
    
    priority_name = priorities.get(priority, "普通优先级")
    
    return f"""问题已升级给人工客服！
优先级: {priority_name}
升级原因: {reason}

人工客服会在工作时间内尽快与您联系，请保持手机畅通。
客服热线: 400-xxx-xxxx"""


# ============ 工具定义 ============

TOOLS = [
    {
        "name": "query_order",
        "description": "查询订单状态和详情，包括商品信息、物流信息等",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单号，例如: ORD-2024-001"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "check_inventory",
        "description": "查询商品库存、价格和 availability",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku_or_name": {
                    "type": "string",
                    "description": "商品SKU或商品名称"
                }
            },
            "required": ["sku_or_name"]
        }
    },
    {
        "name": "process_return",
        "description": "为客户处理退货申请",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "需要退货的订单号"
                },
                "reason": {
                    "type": "string",
                    "description": "退货原因"
                },
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要退货的商品列表（可选，默认全部退货）"
                }
            },
            "required": ["order_id", "reason"]
        }
    },
    {
        "name": "send_message",
        "description": "给客户发送消息或通知",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "客户ID"
                },
                "message": {
                    "type": "string",
                    "description": "消息内容"
                },
                "channel": {
                    "type": "string",
                    "enum": ["app", "sms", "email"],
                    "description": "发送渠道: app(默认), sms, email"
                }
            },
            "required": ["customer_id", "message"]
        }
    },
    {
        "name": "escalate",
        "description": "将复杂问题升级给人工客服处理",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "升级原因"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "description": "优先级: low, normal(默认), high, urgent"
                }
            },
            "required": ["reason"]
        }
    }
]

# 工具处理函数映射
TOOL_HANDLERS = {
    "query_order": query_order,
    "check_inventory": check_inventory,
    "process_return": process_return,
    "send_message": send_message,
    "escalate": escalate
}


# ============ 代理核心循环 ============

def agent_loop(messages: list):
    """
    代理核心循环：与模型交互，根据需要使用工具
    
    核心理念：模型看到上下文和可用工具，决定是行动还是回应
    """
    while True:
        response = client.messages.create(
            model=MODEL,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOLS,
            max_tokens=4000,
            temperature=0.7
        )
        
        # 添加助手回复到历史
        messages.append({"role": "assistant", "content": response.content})
        
        # 如果模型没有调用工具，说明它直接回应了客户
        if response.stop_reason != "tool_use":
            return
        
        # 执行工具调用
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id
                
                print(f"\n🔧 使用工具: {tool_name}")
                print(f"   参数: {json.dumps(tool_input, ensure_ascii=False)}")
                
                # 调用对应的工具函数
                handler = TOOL_HANDLERS.get(tool_name)
                if handler:
                    try:
                        output = handler(**tool_input)
                    except Exception as e:
                        output = f"工具执行错误: {str(e)}"
                else:
                    output = f"未知工具: {tool_name}"
                
                print(f"   结果: {output[:200]}...")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": output
                })
        
        # 将工具结果反馈给模型
        messages.append({"role": "user", "content": tool_results})


# ============ 主程序 ============

def main():
    print("=" * 60)
    print("🛒 电商客服AI助手")
    print("=" * 60)
    print("\n您好！我是您的专属客服助手，很高兴为您服务。")
    print("我可以帮您：")
    print("  • 查询订单状态和物流信息")
    print("  • 查询商品库存和价格")
    print("  • 协助处理退货申请")
    print("  • 解答常见问题")
    print("\n请输入您的问题，或输入 'exit' 退出\n")
    
    # 对话历史
    conversation_history = []
    
    while True:
        try:
            user_input = input("\n👤 客户: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n感谢使用，再见！")
            break
        
        if user_input.lower() in ("exit", "quit", "退出", "再见"):
            print("\n感谢您的咨询，祝您购物愉快！")
            break
        
        if not user_input:
            continue
        
        # 添加用户消息到历史
        conversation_history.append({"role": "user", "content": user_input})
        
        # 运行代理循环
        agent_loop(conversation_history)
        
        # 获取并显示助手的最终回复
        last_message = conversation_history[-1]["content"]
        if isinstance(last_message, list):
            for block in last_message:
                if hasattr(block, "text"):
                    print(f"\n🤖 客服: {block.text}")
        else:
            print(f"\n🤖 客服: {last_message}")


if __name__ == "__main__":
    main()
