"""
Hello 模块 - 打印问候语

这是一个简单的问候程序，用于向用户展示友好的欢迎信息。
"""


def print_greeting() -> None:
    """
    打印问候语到控制台。
    
    该函数输出一条包含中文问候的消息，问候外城和世界。
    
    Returns:
        None: 该函数不返回任何值
    """
    message: str = "你好，外城。你好，世界"
    print(message)


def main() -> None:
    """
    程序的主入口函数。
    
    负责协调程序的执行流程，调用问候函数。
    
    Returns:
        None: 该函数不返回任何值
    """
    print_greeting()


if __name__ == "__main__":
    main()
