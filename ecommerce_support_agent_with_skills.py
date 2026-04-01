#!/usr/bin/env python3
"""
ecommerce_support_agent_with_skills.py - 带技能系统的电商客服代理

改进点：
1. 使用技能系统按需加载知识，避免系统提示词膨胀
2. 两层知识注入：Layer 1(元数据) + Layer 2(完整内容)
3. 模型自主决定何时加载技能

核心理念：知识按需加载，保持上下文清晰。
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
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

# ============ 技能系统 ============

SKILLS_DIR = Path(__file__).parent / "skills" / "ecommerce-support"


class SkillLoader:
    """
    技能加载器 - 两层知识注入
    
    Layer 1 (cheap): 技能元数据在系统提示中 (~50 tokens/skill)
    Layer 2 (on demand): 完整技能内容在 tool_result 中按需加载
    """
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills = {}
        self._load_all()
    
    def _load_all(self):
        """加载所有技能文件"""
        if not self.skills_dir.exists():
            return
        
        for f in sorted(self.skills_dir.glob("*.md")):
            text = f.read_text()
            meta, body = self._parse_frontmatter(text)
            name = meta.get("name", f.stem)
            self.skills[name] = {
                "meta": meta,
                "body": body,
                "path": str(f)
            }
    
    def _parse_frontmatter(self, text: str) -> tuple:
        """解析 frontmatter (--- 之间的 YAML)"""
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        
        # 简单解析 YAML (不使用 yaml 库，减少依赖)
        meta_text = match.group(1)
        meta = {}
        for line in meta_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
        
        return meta, match.group(2).strip()
    
    def get_descriptions(self) -> str:
        """Layer 1: 技能描述列表，用于系统提示"""
        if not self.skills:
            return "(暂无可用技能)"
        
        lines = []
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "无描述")
            lines.append(f"  - {name}: {desc}")
        return "\n".join(lines)
    
    def get_content(self, name: str) -> str:
        """Layer 2: 完整技能内容，按需加载"""
        skill = self.skills.get(name)
        if not skill:
            available = ", ".join(self.skills.keys())
            return f"错误: 未知技能 '{name}'。可用技能: {available}"
        
        return f"<skill name=\"{name}\">\n{skill['body']}\n</skill>"


# 初始化技能加载器
SKILL_LOADER = SkillLoader(SKILLS_DIR)


# ============ 模拟数据库 ============

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

RETURNS_DB = {}


# ============ 系统提示词 (Layer 1: 只包含技能元数据) ============

SYSTEM_PROMPT = f"""你是专业的电商客服AI助手。

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
- query_order: 查询订单状态和详情
- check_inventory: 查询商品库存和价格
- process_return: 处理退货申请
- send_message: 给客户发送通知或消息
- escalate: 将问题升级给人工客服
- load_skill: 加载专业知识（重要：遇到专业问题时先加载技能）

## 可用技能（按需加载）
{SKILL_LOADER.get_descriptions()}

## 使用技能的指导
当客户询问以下类型问题时，**必须先加载对应技能**：
- 退换货政策、流程 → 加载 return-policy
- 配送时效、物流 → 加载 shipping-info
- 保修、真伪、规格 → 加载 product-faq

**不要凭记忆回答专业问题，必须加载技能获取准确信息。**

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
    if sku_or_name in INVENTORY_DB:
        item = INVENTORY_DB[sku_or_name]
        stock_status = "有货" if item["stock"] > 0 else "暂时缺货"
        return f"""商品: {item['name']}
SKU: {sku_or_name}
价格: ¥{item['price']}
库存: {item['stock']} 件
状态: {stock_status}
分类: {item['category']}"""
    
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
    
    if order["status"] not in ["已完成", "已发货"]:
        return f"订单状态为 '{order['status']}'，暂不符合退货条件。"
    
    return_id = f"RET-{order_id}-{datetime.now().strftime('%Y%m%d')}"
    
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


def load_skill(name: str) -> str:
    """加载专业技能知识 (Layer 2: 按需加载完整内容)"""
    return SKILL_LOADER.get_content(name)


# ============ 工具定义 ============

TOOLS = [
    {
        "name": "query_order",
        "description": "查询订单状态和详情，包括商品信息、物流信息等",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "订单号，例如: ORD-2024-001"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "check_inventory",
        "description": "查询商品库存和价格",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku_or_name": {"type": "string", "description": "商品SKU或商品名称"}
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
                "order_id": {"type": "string", "description": "需要退货的订单号"},
                "reason": {"type": "string", "description": "退货原因"},
                "items": {"type": "array", "items": {"type": "string"}, "description": "需要退货的商品列表（可选）"}
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
                "customer_id": {"type": "string", "description": "客户ID"},
                "message": {"type": "string", "description": "消息内容"},
                "channel": {"type": "string", "enum": ["app", "sms", "email"], "description": "发送渠道"}
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
                "reason": {"type": "string", "description": "升级原因"},
                "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "description": "优先级"}
            },
            "required": ["reason"]
        }
    },
    {
        "name": "load_skill",
        "description": "加载专业技能知识。当客户询问退换货政策、配送时效、保修等专业知识时，必须先加载对应技能。",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "技能名称: return-policy(退换货), shipping-info(配送), product-faq(商品FAQ)"}
            },
            "required": ["name"]
        }
    }
]

TOOL_HANDLERS = {
    "query_order": query_order,
    "check_inventory": check_inventory,
    "process_return": process_return,
    "send_message": send_message,
    "escalate": escalate,
    "load_skill": load_skill
}


# ============ 代理核心循环 ============

def agent_loop(messages: list):
    """代理核心循环"""
    while True:
        response = client.messages.create(
            model=MODEL,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOLS,
            max_tokens=4000,
            temperature=0.7
        )
        
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            return
        
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id
                
                print(f"\n🔧 使用工具: {tool_name}")
                if tool_name == "load_skill":
                    print(f"   📚 加载技能: {tool_input.get('name', 'unknown')}")
                else:
                    print(f"   参数: {json.dumps(tool_input, ensure_ascii=False)}")
                
                handler = TOOL_HANDLERS.get(tool_name)
                if handler:
                    try:
                        output = handler(**tool_input)
                    except Exception as e:
                        output = f"工具执行错误: {str(e)}"
                else:
                    output = f"未知工具: {tool_name}"
                
                # 截断显示
                display_output = output[:150] + "..." if len(output) > 150 else output
                print(f"   结果: {display_output}")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": output
                })
        
        messages.append({"role": "user", "content": tool_results})


# ============ 主程序 ============

def main():
    print("=" * 60)
    print("🛒 电商客服AI助手 (带技能系统)")
    print("=" * 60)
    print("\n您好！我是您的专属客服助手。")
    print("\n我可以帮您：")
    print("  • 查询订单状态和物流信息")
    print("  • 查询商品库存和价格")
    print("  • 协助处理退货申请")
    print("  • 解答退换货、配送、保修等专业问题")
    print("\n💡 我会自动加载专业知识来回答您的问题")
    print("\n请输入您的问题，或输入 'exit' 退出\n")
    
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
        
        conversation_history.append({"role": "user", "content": user_input})
        
        agent_loop(conversation_history)
        
        last_message = conversation_history[-1]["content"]
        if isinstance(last_message, list):
            for block in last_message:
                if hasattr(block, "text"):
                    print(f"\n🤖 客服: {block.text}")
        else:
            print(f"\n🤖 客服: {last_message}")


if __name__ == "__main__":
    main()
