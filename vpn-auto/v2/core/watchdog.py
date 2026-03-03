#!/usr/bin/env python3
"""
VPN 监控守护进程 - 状态机核心
负责监控 VPN 连接状态并触发重连
"""

import time
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.network_check import NetworkChecker
from core.orchestrator import ReconnectOrchestrator
from core.config_loader import load_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VPNWatchdog:
    """VPN 监控守护进程"""
    
    def __init__(self, config_path=None):
        """初始化"""
        self.config = load_config(config_path)
        self.network_checker = NetworkChecker(self.config)
        self.orchestrator = ReconnectOrchestrator(self.config)
        self.consecutive_failures = 0
        self.max_failures = self.config['reconnect']['max_failures']
        self.check_interval = self.config['network']['check_interval']
        
        logger.info("VPN Watchdog 已启动")
        logger.info(f"检测间隔: {self.check_interval} 秒")
        logger.info(f"最大失败次数: {self.max_failures}")
    
    def run(self):
        """主循环"""
        while True:
            try:
                if self.network_checker.is_vpn_connected():
                    # VPN 正常
                    if self.consecutive_failures > 0:
                        logger.info("✅ VPN 已恢复连接")
                    self.consecutive_failures = 0
                    logger.debug("VPN 状态正常")
                else:
                    # VPN 断开
                    self.consecutive_failures += 1
                    logger.warning(f"⚠️  VPN 断开 (失败次数: {self.consecutive_failures}/{self.max_failures})")
                    
                    if self.consecutive_failures >= self.max_failures:
                        logger.error(f"❌ VPN 连续失败 {self.consecutive_failures} 次，触发重连")
                        self.trigger_reconnect()
                
                # 等待下一次检测
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，退出...")
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}", exc_info=True)
                time.sleep(self.check_interval)
    
    def trigger_reconnect(self):
        """触发重连"""
        try:
            logger.info("=" * 60)
            logger.info("开始 VPN 重连流程")
            logger.info("=" * 60)
            
            success = self.orchestrator.reconnect()
            
            if success:
                logger.info("=" * 60)
                logger.info("✅ VPN 重连成功")
                logger.info("=" * 60)
                self.consecutive_failures = 0
            else:
                logger.error("=" * 60)
                logger.error("❌ VPN 重连失败")
                logger.error("=" * 60)
                # 不重置失败计数，下次循环继续尝试
        
        except Exception as e:
            logger.error(f"重连流程异常: {e}", exc_info=True)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VPN 监控守护进程')
    parser.add_argument('-c', '--config', help='配置文件路径')
    args = parser.parse_args()
    
    watchdog = VPNWatchdog(config_path=args.config)
    watchdog.run()


if __name__ == '__main__':
    main()
