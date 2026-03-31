"""
包级别的单元测试

测试包的导入和基本功能。
"""

import unittest
import mypackage


class TestPackageImports(unittest.TestCase):
    """测试包的导入"""
    
    def test_version_exists(self) -> None:
        """测试版本号存在"""
        self.assertTrue(hasattr(mypackage, "__version__"))
        self.assertIsInstance(mypackage.__version__, str)
    
    def test_author_exists(self) -> None:
        """测试作者存在"""
        self.assertTrue(hasattr(mypackage, "__author__"))
        self.assertIsInstance(mypackage.__author__, str)
    
    def test_greet_import(self) -> None:
        """测试 greet 函数可导入"""
        self.assertTrue(hasattr(mypackage, "greet"))
        self.assertTrue(callable(mypackage.greet))
    
    def test_format_message_import(self) -> None:
        """测试 format_message 函数可导入"""
        self.assertTrue(hasattr(mypackage, "format_message"))
        self.assertTrue(callable(mypackage.format_message))


class TestPackageFunctions(unittest.TestCase):
    """测试包的公共函数"""
    
    def test_greet_via_package(self) -> None:
        """测试通过包调用 greet"""
        result = mypackage.greet("测试")
        self.assertEqual(result, "你好，测试")
    
    def test_format_message_via_package(self) -> None:
        """测试通过包调用 format_message"""
        result = mypackage.format_message("test", prefix="[DEBUG] ")
        self.assertEqual(result, "[DEBUG] test")


if __name__ == "__main__":
    unittest.main()
