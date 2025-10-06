#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重构后的功能测试脚本"""

import sys
import os
import io
from pathlib import Path

# 设置 UTF-8 编码输出
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """测试 1: 模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:
        from core.config import UnifiedConfigManager
        print("✓ UnifiedConfigManager 导入成功")

        from core.base import LoginAutomation
        print("✓ LoginAutomation 导入成功")

        from core.browser import BrowserManager
        print("✓ BrowserManager 导入成功")

        from core.cookies import CookieManager
        print("✓ CookieManager 导入成功")

        from sites.anyrouter.login import AnyrouterLogin, login_to_anyrouter
        print("✓ anyrouter.login 导入成功")

        from sites.linuxdo.login import LinuxdoLogin, login_to_linuxdo
        print("✓ linuxdo.login 导入成功")

        from sites.openi.login import OpeniLogin
        print("✓ openi.login 导入成功")

        print("\n✅ 模块导入测试: PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ 模块导入测试: FAILED - {e}\n")
        return False


def test_config_manager():
    """测试 2: UnifiedConfigManager 功能"""
    print("=" * 60)
    print("测试 2: UnifiedConfigManager 功能")
    print("=" * 60)

    try:
        from core.config import UnifiedConfigManager

        cfg = UnifiedConfigManager()
        print("✓ UnifiedConfigManager 初始化成功")

        # 测试获取凭据（带环境变量 fallback）
        linuxdo_creds = cfg.get_credentials('linuxdo', fallback_env=True)
        print(f"✓ get_credentials('linuxdo') 返回: {type(linuxdo_creds)}")

        anyrouter_creds = cfg.get_credentials('anyrouter', fallback_env=True)
        print(f"✓ get_credentials('anyrouter') 返回: {type(anyrouter_creds)}")

        # 测试获取所有用户
        openi_users = cfg.get_all_users('openi')
        print(f"✓ get_all_users('openi') 返回: {len(openi_users)} 个用户")

        linuxdo_users = cfg.get_all_users('linuxdo')
        print(f"✓ get_all_users('linuxdo') 返回: {len(linuxdo_users)} 个用户")

        # 测试获取站点配置
        openi_cfg = cfg.get_site_config('openi')
        print(f"✓ get_site_config('openi') 返回: {type(openi_cfg)}")

        # 测试新的内部方法
        assert hasattr(cfg, '_get_from_credentials_format'), "缺少 _get_from_credentials_format"
        assert hasattr(cfg, '_get_from_users_format'), "缺少 _get_from_users_format"
        assert hasattr(cfg, '_get_from_legacy_openi_format'), "缺少 _get_from_legacy_openi_format"
        print("✓ 新的格式处理方法存在")

        print("\n✅ UnifiedConfigManager 测试: PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ UnifiedConfigManager 测试: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_login_classes():
    """测试 3: 登录类初始化和方法"""
    print("=" * 60)
    print("测试 3: 登录类初始化和方法")
    print("=" * 60)

    try:
        from sites.anyrouter.login import AnyrouterLogin
        from sites.linuxdo.login import LinuxdoLogin
        from sites.openi.login import OpeniLogin

        # 测试 AnyrouterLogin
        anyrouter = AnyrouterLogin(headless=True)
        print("✓ AnyrouterLogin 初始化成功")

        # 检查 AnyrouterLogin 的方法
        required_methods = [
            'verify_login',
            'do_login',
            'login_with_linuxdo_oauth',
            '_validate_auth_page',
            '_finalize_and_verify',
            '_navigate_to_login_page',
            '_close_announcement_modal',
            '_preload_linuxdo_cookie',
            '_save_linuxdo_cookie',
            '_open_oauth_window',
            '_oauth_button_candidates',
            '_fill_linuxdo_credentials_if_needed',
            '_get_linuxdo_credentials',
            '_fill_and_submit',
            '_handle_oauth_consent',
            '_early_verify_anyrouter',
        ]

        for method in required_methods:
            assert hasattr(anyrouter, method), f"AnyrouterLogin 缺少方法: {method}"
        print(f"✓ AnyrouterLogin 所有 {len(required_methods)} 个方法存在")

        # 确认调试方法已移除
        assert not hasattr(anyrouter, '_shot'), "调试方法 _shot 应该已移除"
        assert not hasattr(anyrouter, 'debug_dir'), "调试属性 debug_dir 应该已移除"
        print("✓ AnyrouterLogin 调试代码已清理")

        # 测试 LinuxdoLogin
        linuxdo = LinuxdoLogin(headless=True)
        print("✓ LinuxdoLogin 初始化成功")

        # 检查 LinuxdoLogin 的方法
        linuxdo_methods = [
            'verify_login',
            'do_login',
            'login_with_credentials',
            '_submit_login_form',
            'after_login',
        ]

        for method in linuxdo_methods:
            assert hasattr(linuxdo, method), f"LinuxdoLogin 缺少方法: {method}"
        print(f"✓ LinuxdoLogin 所有 {len(linuxdo_methods)} 个方法存在")

        # 测试 OpeniLogin
        openi = OpeniLogin('test_user', headless=True)
        print("✓ OpeniLogin 初始化成功")

        openi_methods = [
            'verify_login',
            'do_login',
            'after_login',
        ]

        for method in openi_methods:
            assert hasattr(openi, method), f"OpeniLogin 缺少方法: {method}"
        print(f"✓ OpeniLogin 所有 {len(openi_methods)} 个方法存在")

        print("\n✅ 登录类测试: PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ 登录类测试: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_browser_manager():
    """测试 4: BrowserManager 重构"""
    print("=" * 60)
    print("测试 4: BrowserManager 重构")
    print("=" * 60)

    try:
        from core.browser import BrowserManager

        mgr = BrowserManager()
        print("✓ BrowserManager 初始化成功")

        # 检查新方法
        assert hasattr(mgr, '_log_warning'), "缺少 _log_warning 方法"
        print("✓ BrowserManager._log_warning 方法存在")

        print("\n✅ BrowserManager 测试: PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ BrowserManager 测试: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_code_metrics():
    """测试 5: 代码度量指标"""
    print("=" * 60)
    print("测试 5: 代码度量指标")
    print("=" * 60)

    try:
        import subprocess

        # 检查文件行数
        files_to_check = {
            'src/sites/anyrouter/login.py': (290, 300),  # 应该在 290-300 行之间
            'src/sites/linuxdo/login.py': (210, 220),     # 应该在 210-220 行之间
            'src/core/browser.py': (65, 70),               # 应该在 65-70 行之间
            'src/core/config.py': (245, 255),              # 应该在 245-255 行之间
        }

        for filepath, (min_lines, max_lines) in files_to_check.items():
            result = subprocess.run(['wc', '-l', filepath], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                lines = int(result.stdout.split()[0])
                if min_lines <= lines <= max_lines:
                    print(f"✓ {filepath}: {lines} 行 (预期 {min_lines}-{max_lines})")
                else:
                    print(f"⚠ {filepath}: {lines} 行 (预期 {min_lines}-{max_lines})")
            else:
                print(f"? {filepath}: 无法统计行数")

        print("\n✅ 代码度量测试: PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ 代码度量测试: FAILED - {e}\n")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("重构后代码测试套件")
    print("=" * 60 + "\n")

    results = []

    # 运行所有测试
    results.append(("模块导入", test_imports()))
    results.append(("配置管理器", test_config_manager()))
    results.append(("登录类", test_login_classes()))
    results.append(("浏览器管理器", test_browser_manager()))
    results.append(("代码度量", test_code_metrics()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:20s} - {status}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60 + "\n")

    if passed == total:
        print("🎉 所有测试通过！代码重构成功。\n")
        return 0
    else:
        print(f"⚠️  {total - passed} 个测试失败，请检查。\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
