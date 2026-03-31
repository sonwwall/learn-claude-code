#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花式欢迎模块 - 打印"你好，外城"
"""

import random


def greet_fancy(name: str = "外城") -> None:
    """
    花式打印欢迎信息
    
    Args:
        name: 欢迎对象名称，默认为"外城"
    """
    styles = [
        _style_banner,
        _style_emoji,
        _style_ascii_art,
        _style_box,
        _style_wave,
        _style_gradient,
        _style_fireworks,
    ]
    
    # 随机选择一种风格
    chosen_style = random.choice(styles)
    chosen_style(name)


def _style_banner(name: str) -> None:
    """横幅风格"""
    message = f"你好，{name}"
    border = "=" * (len(message) * 2 + 6)
    print(f"\n{border}")
    print(f"===  {message}  ===")
    print(f"{border}\n")


def _style_emoji(name: str) -> None:
    """表情风格"""
    emojis = ["🎉", "✨", "🌟", "💫", "🎊", "🌈", "🔥", "⭐"]
    left = random.sample(emojis, 3)
    right = random.sample(emojis, 3)
    print(f"\n{' '.join(left)}  你好，{name}  {' '.join(right)}\n")


def _style_ascii_art(name: str) -> None:
    """ASCII艺术风格"""
    art = f"""
    ♪ ┏(・o･)┛ ♪ ┗ ( ・o･)┓ ♪
         
         你好，{name}
         
    ♪ ┏(・o･)┛ ♪ ┗ ( ・o･)┓ ♪
    """
    print(art)


def _style_box(name: str) -> None:
    """盒子风格"""
    message = f"你好，{name}"
    width = len(message) + 4
    print()
    print("┌" + "─" * width + "┐")
    print("│" + " " * width + "│")
    print(f"│  {message}  │")
    print("│" + " " * width + "│")
    print("└" + "─" * width + "┘")
    print()


def _style_wave(name: str) -> None:
    """波浪风格"""
    message = f"你好，{name}"
    print()
    print("~" * 30)
    print(f"  ≋≋≋ {message} ≋≋≋  ")
    print("~" * 30)
    print()


def _style_gradient(name: str) -> None:
    """渐变符号风格"""
    symbols = ["░", "▒", "▓", "█", "▓", "▒", "░"]
    message = f"  你好，{name}  "
    print()
    print("".join(symbols) + message + "".join(reversed(symbols)))
    print()


def _style_fireworks(name: str) -> None:
    """烟花风格"""
    fireworks = [
        "       \|/",
        "     \\|/  你好，" + name,
        "    --*--",
        "     /|\\",
        "    / | \\",
    ]
    print()
    for line in fireworks:
        print(line)
    print()


def greet_all() -> None:
    """展示所有风格"""
    name = "外城"
    print("\n" + "=" * 50)
    print("        花式欢迎展示 - 你好，外城")
    print("=" * 50 + "\n")
    
    styles = [
        ("横幅风格", _style_banner),
        ("表情风格", _style_emoji),
        ("ASCII艺术", _style_ascii_art),
        ("盒子风格", _style_box),
        ("波浪风格", _style_wave),
        ("渐变风格", _style_gradient),
        ("烟花风格", _style_fireworks),
    ]
    
    for style_name, style_func in styles:
        print(f"【{style_name}】")
        style_func(name)
        print("-" * 40)


if __name__ == "__main__":
    # 默认随机展示一种风格
    print("\n🎲 随机选择一种风格：")
    greet_fancy("外城")
    
    # 展示所有风格
    input("\n按回车键查看所有风格...")
    greet_all()
