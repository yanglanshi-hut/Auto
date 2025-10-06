"""
测试脚本：演示如何先登录 LinuxDO，然后使用 OAuth 登录 AnyRouter
"""

import sys
import os

# 添加 linuxdo 脚本路径到系统路径
linuxdo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'linuxdo')
sys.path.insert(0, linuxdo_path)

from src.sites.anyrouter.login import login_to_anyrouter

if __name__ == "__main__":
    print("=" * 60)
    print("AnyRouter 登录测试")
    print("=" * 60)

    print("\n注意：请确保已经登录 LinuxDO")
    print("如果还未登录，请先运行: python ../linuxdo/linuxdo_login.py\n")

    response = input("是否已经登录 LinuxDO？(y/n): ")

    if response.lower() != 'y':
        print("\n请先运行 LinuxDO 登录脚本：")
        print("cd ../linuxdo && python linuxdo_login.py")
        sys.exit(0)

    print("\n开始登录 AnyRouter...\n")

    # 执行 AnyRouter 登录
    login_to_anyrouter(
        use_cookie=True,
        headless=False
    )

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

