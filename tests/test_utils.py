"""
工具模块的单元测试

测试 utils.py 中的所有函数。
"""

import unittest
from mypackage.utils import greet, format_message, get_package_info


class TestGreetFunction(unittest.TestCase):
    """测试 greet 函数"""
    
    def test_default_greeting(self) -> None:
        """测试默认问候语"""
        result = greet("世界")
        self.assertEqual(result, "你好，世界")
    
    def test_custom_greeting(self) -> None:
        """测试自定义问候语"""
        result = greet("Python", "Hello")
        self.assertEqual(result, "Hello，Python")
    
    def test_empty_name(self) -> None:
        """测试空名称"""
        result = greet("")
        self.assertEqual(result, "你好，")


class TestFormatMessageFunction(unittest.TestCase):
    """测试 format_message 函数"""
    
    def test_no_modifications(self) -> None:
        """测试无修改的情况"""
        result = format_message("hello")
        self.assertEqual(result, "hello")
    
    def test_with_prefix(self) -> None:
        """测试添加前缀"""
        result = format_message("hello", prefix="[INFO] ")
        self.assertEqual(result, "[INFO] hello")
    
    def test_with_suffix(self) -> None:
        """测试添加后缀"""
        result = format_message("hello", suffix="!")
        self.assertEqual(result, "hello!")
    
    def test_uppercase(self) -> None:
        """测试转换为大写"""
        result = format_message("hello", uppercase=True)
        self.assertEqual(result, "HELLO")
    
    def test_all_modifications(self) -> None:
        """测试所有修改组合"""
        result = format_message(
            "hello",
            prefix="[TEST] ",
            suffix="...",
            uppercase=True
        )
        self.assertEqual(result, "[TEST] HELLO...")


class TestGetPackageInfoFunction(unittest.TestCase):
    """测试 get_package_info 函数"""
    
    def test_return_type(self) -> None:
        """测试返回类型"""
        result = get_package_info()
        self.assertIsInstance(result, dict)
    
    def test_required_keys(self) -> None:
        """测试必需的键"""
        result = get_package_info()
        required_keys = ["name", "description", "version"]
        for key in required_keys:
            self.assertIn(key, result)
    
    def test_name_value(self) -> None:
        """测试 name 值"""
        result = get_package_info()
        self.assertEqual(result["name"], "mypackage")


if __name__ == "__main__":
    unittest.main()
