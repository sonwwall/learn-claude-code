"""
工具模块 - 提供各种实用函数

该模块包含字符串处理和格式化相关的工具函数。
"""

from typing import Optional


def greet(name: str, greeting: str = "你好") -> str:
    """
    生成问候语。

    Args:
        name: 被问候的对象名称
        greeting: 问候语前缀，默认为 "你好"

    Returns:
        格式化后的问候字符串

    Example:
        >>> greet("世界")
        '你好，世界'
        >>> greet("Python", "Hello")
        'Hello，Python'
    """
    return f"{greeting}，{name}"


def format_message(
    message: str,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    uppercase: bool = False
) -> str:
    """
    格式化消息字符串。

    Args:
        message: 原始消息内容
        prefix: 可选的前缀字符串
        suffix: 可选的后缀字符串
        uppercase: 是否转换为大写，默认为 False

    Returns:
        格式化后的消息字符串

    Example:
        >>> format_message("hello", prefix="[INFO] ")
        '[INFO] hello'
        >>> format_message("hello", uppercase=True)
        'HELLO'
    """
    result = message
    
    if prefix:
        result = prefix + result
    
    if suffix:
        result = result + suffix
    
    if uppercase:
        result = result.upper()
    
    return result


def get_package_info() -> dict[str, str]:
    """
    获取包的基本信息。

    Returns:
        包含包信息的字典
    """
    return {
        "name": "mypackage",
        "description": "示例 Python 包",
        "version": "1.0.0"
    }
