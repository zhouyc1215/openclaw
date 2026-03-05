#!/usr/bin/env python3
"""
测试三个驱动的功能
"""

import os
import sys
import yaml
import logging

# 设置环境变量
os.environ['DISPLAY'] = ':1'
os.environ['QT_ACCESSIBILITY'] = '1'
os.environ['QT_LINUX_ACCESSIBILITY_ALWAYS_ON'] = '1'

# 添加项目路径
sys.path.insert(0, '/home/tsl/openclaw/vpn-auto/v2')

from drivers.atspi_driver import ATSPIDriver
from drivers.pyauto_driver import PyAutoDriver
from drivers.vision_driver import VisionDriver

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def load_config():
    """加载配置"""
    config_path = '/home/tsl/openclaw/vpn-auto/v2/config/config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_atspi_driver(config):
    """测试 ATSPIDriver"""
    print("\n" + "=" * 60)
    print("测试 1: ATSPIDriver")
    print("=" * 60)
    
    try:
        driver = ATSPIDriver(config)
        
        if not driver.available:
            print("❌ ATSPIDriver 不可用（缺少依赖）")
            return False
        
        print("✅ ATSPIDriver 已加载")
        print("尝试点击连接按钮...")
        
        result = driver.click_connect()
        
        if result:
            print("✅ ATSPIDriver 测试成功")
            return True
        else:
            print("❌ ATSPIDriver 测试失败")
            return False
    
    except Exception as e:
        print(f"❌ ATSPIDriver 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pyauto_driver(config):
    """测试 PyAutoDriver"""
    print("\n" + "=" * 60)
    print("测试 2: PyAutoDriver")
    print("=" * 60)
    
    try:
        driver = PyAutoDriver(config)
        
        if not driver.available:
            print("❌ PyAutoDriver 不可用（缺少依赖）")
            return False
        
        print("✅ PyAutoDriver 已加载")
        print(f"按钮图像: {driver.button_image}")
        print(f"置信度: {driver.confidence}")
        
        # 检查按钮图像是否存在
        if not os.path.exists(driver.button_image):
            print(f"❌ 按钮图像不存在: {driver.button_image}")
            return False
        
        print("✅ 按钮图像存在")
        print("尝试点击连接按钮...")
        
        result = driver.click_connect()
        
        if result:
            print("✅ PyAutoDriver 测试成功")
            return True
        else:
            print("❌ PyAutoDriver 测试失败")
            return False
    
    except Exception as e:
        print(f"❌ PyAutoDriver 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vision_driver(config):
    """测试 VisionDriver"""
    print("\n" + "=" * 60)
    print("测试 3: VisionDriver")
    print("=" * 60)
    
    try:
        driver = VisionDriver(config)
        
        if not driver.available:
            print("❌ VisionDriver 不可用（缺少依赖）")
            return False
        
        print("✅ VisionDriver 已加载")
        print("尝试点击连接按钮...")
        
        result = driver.click_connect()
        
        if result:
            print("✅ VisionDriver 测试成功")
            return True
        else:
            print("❌ VisionDriver 测试失败")
            return False
    
    except Exception as e:
        print(f"❌ VisionDriver 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("VPN 驱动测试工具")
    print("=" * 60)
    print()
    print("环境变量:")
    print(f"  DISPLAY: {os.environ.get('DISPLAY')}")
    print(f"  QT_ACCESSIBILITY: {os.environ.get('QT_ACCESSIBILITY')}")
    print(f"  QT_LINUX_ACCESSIBILITY_ALWAYS_ON: {os.environ.get('QT_LINUX_ACCESSIBILITY_ALWAYS_ON')}")
    print()
    
    # 加载配置
    print("加载配置...")
    config = load_config()
    print("✅ 配置已加载")
    print()
    
    # 测试三个驱动
    results = {
        'ATSPIDriver': test_atspi_driver(config),
        'PyAutoDriver': test_pyauto_driver(config),
        'VisionDriver': test_vision_driver(config)
    }
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print()
    
    for driver_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{driver_name:20s} {status}")
    
    print()
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"成功: {success_count}/{total_count}")
    print()
    
    if success_count == 0:
        print("⚠️  所有驱动都失败了")
        sys.exit(1)
    elif success_count < total_count:
        print("⚠️  部分驱动失败")
        sys.exit(0)
    else:
        print("🎉 所有驱动都成功了！")
        sys.exit(0)


if __name__ == '__main__':
    main()
