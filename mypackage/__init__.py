"""
MyPackage - 示例 Python 包

这是一个用于演示的 Python 包，包含问候功能和工具函数。

Example:
    >>> from mypackage import greet
    >>> greet("世界")
    '你好，世界'

Attributes:
    __version__ (str): 包的版本号
    __author__ (str): 包的作者
"""

from .utils import greet, format_message

__version__ = "1.0.0"
__author__ = "Developer"

__all__ = ["greet", "format_message", "__version__", "__author__"]
