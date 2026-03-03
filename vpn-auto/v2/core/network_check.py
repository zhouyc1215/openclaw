#!/usr/bin/env python3
"""
网络检测模块
提供多重网络检测机制
"""

import subprocess
import logging

logger = logging.getLogger(__name__)


class NetworkChecker:
    """网络检测器"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config
        self.check_hosts = config['network']['check_hosts']
        self.ping_count = config['network']['ping_count']
        self.ping_timeout = config['network']['ping_timeout']
        self.vpn_interface = config['network']['vpn_interface']
    
    def is_vpn_connected(self):
        """检查 VPN 是否连接"""
        # 方法 1: 检查 VPN 网络接口
        if self.check_vpn_interface():
            # 方法 2: 检查网络连通性
            if self.check_network_connectivity():
                return True
        
        return False
    
    def check_vpn_interface(self):
        """检查 VPN 网络接口是否存在"""
        try:
            # 方法 1: 使用 forticlient vpn status 命令（最准确）
            result = subprocess.run(
                ['forticlient', 'vpn', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and 'Status: Connected' in result.stdout:
                logger.debug(f"✅ FortiClient VPN 已连接")
                return True
            
            # 方法 2: 检查指定的接口名称
            result = subprocess.run(
                ['ip', 'addr', 'show', self.vpn_interface],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and 'inet ' in result.stdout:
                logger.debug(f"✅ VPN 接口 {self.vpn_interface} 存在")
                return True
            
            # 方法 3: 如果指定接口不存在，尝试查找 fctvpn 开头的接口
            if 'ppp' in self.vpn_interface or 'fctvpn' in self.vpn_interface:
                result = subprocess.run(
                    ['ip', 'addr', 'show'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # 查找 fctvpn 开头的接口
                for line in result.stdout.split('\n'):
                    if 'fctvpn' in line and 'inet ' in line:
                        logger.debug(f"✅ 找到 FortiClient VPN 接口")
                        return True
                    # 也检查下一行是否有 inet 地址
                    if 'fctvpn' in line:
                        # 获取接口名称
                        import re
                        match = re.search(r'(\d+): (fctvpn\w+):', line)
                        if match:
                            iface = match.group(2)
                            # 检查这个接口是否有 IP 地址
                            iface_result = subprocess.run(
                                ['ip', 'addr', 'show', iface],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if 'inet ' in iface_result.stdout:
                                logger.debug(f"✅ VPN 接口 {iface} 存在")
                                return True
            
            logger.debug(f"❌ VPN 接口不存在")
            return False
        
        except Exception as e:
            logger.error(f"检查 VPN 接口失败: {e}")
            return False
    
    def check_network_connectivity(self):
        """检查网络连通性"""
        for host in self.check_hosts:
            if self.ping_host(host):
                logger.debug(f"✅ 可以访问 {host}")
                return True
        
        logger.debug(f"❌ 无法访问任何检测主机")
        return False
    
    def ping_host(self, host):
        """Ping 主机"""
        try:
            result = subprocess.run(
                ['ping', '-c', str(self.ping_count), '-W', str(self.ping_timeout), host],
                capture_output=True,
                text=True,
                timeout=self.ping_timeout + 5
            )
            
            return result.returncode == 0
        
        except Exception as e:
            logger.debug(f"Ping {host} 失败: {e}")
            return False
