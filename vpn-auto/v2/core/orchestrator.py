#!/usr/bin/env python3
"""
重连策略编排器
负责协调整个重连流程
"""

import time
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from drivers.atspi_driver import ATSPIDriver
from drivers.pyauto_driver import PyAutoDriver
from drivers.vision_driver import VisionDriver
from core.feishu_notifier import FeishuNotifier

logger = logging.getLogger(__name__)


class ReconnectOrchestrator:
    """重连策略编排器"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config
        self.display = config['system']['display']
        self.sudo_password = config['system']['sudo_password']
        
        # 初始化驱动
        self.drivers = self._init_drivers()
        
        # 初始化飞书通知器
        self.feishu = FeishuNotifier(config)
        
        logger.info(f"已加载 {len(self.drivers)} 个驱动")
    
    def _init_drivers(self):
        """初始化驱动"""
        drivers = []
        
        for driver_name in self.config['drivers']['priority']:
            driver_config = self.config['drivers'].get(driver_name, {})
            
            if not driver_config.get('enabled', True):
                logger.info(f"驱动 {driver_name} 已禁用")
                continue
            
            if driver_name == 'atspi':
                drivers.append(ATSPIDriver(self.config))
            elif driver_name == 'pyauto':
                drivers.append(PyAutoDriver(self.config))
            elif driver_name == 'vision':
                drivers.append(VisionDriver(self.config))
            else:
                logger.warning(f"未知驱动: {driver_name}")
        
        return drivers
    
    def reconnect(self):
        """执行重连流程"""
        try:
            # 1. 停止 FortiClient
            if not self.stop_forticlient():
                logger.error("停止 FortiClient 失败")
                return False
            
            # 2. 启动 FortiClient
            if not self.start_forticlient():
                logger.error("启动 FortiClient 失败")
                return False
            
            # 3. 等待窗口出现
            if not self.wait_for_window():
                logger.error("FortiClient 窗口未出现")
                return False
            
            # 4. 等待 GUI 加载
            gui_delay = self.config['reconnect']['gui_load_delay']
            logger.info(f"等待 GUI 加载 ({gui_delay} 秒)...")
            time.sleep(gui_delay)
            
            # 6. 点击连接按钮（尝试所有驱动）
            button_clicked = self.click_connect_button()
            if not button_clicked:
                logger.error("点击连接按钮失败")
                return False
            
            # 7. 等待 VPN 连接
            vpn_connected = self.wait_for_vpn_connection()
            
            # 8. 如果 VPN 连接成功，返回成功
            if vpn_connected:
                return True
            
            # 9. 如果按钮点击成功但 VPN 未连接，说明需要手动 SAML 认证
            if button_clicked and not vpn_connected:
                logger.warning("⚠️  VPN 需要手动完成 SAML 认证")
                # 发送截图到飞书
                self.feishu.take_screenshot_and_send(
                    caption="⚠️ VPN 需要手动完成 SAML 认证\n"
                            "请在浏览器中完成认证流程"
                )
                return False
            
            return vpn_connected
        
        except Exception as e:
            logger.error(f"重连流程异常: {e}", exc_info=True)
            return False
    
    def stop_forticlient(self):
        """停止 FortiClient"""
        logger.info("停止 FortiClient 进程...")
        
        try:
            # 尝试使用 sudo 免密码模式
            result = subprocess.run(
                ['sudo', '-n', 'pkill', '-9', '-f', 'forticlient'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            logger.debug(f"sudo pkill 返回码: {result.returncode}")
            
            # 返回码 0 表示成功杀死进程
            # 返回码 1 表示没有找到进程（也算成功）
            # 返回码 137 表示进程被杀死（也算成功）
            if result.returncode in [0, 1, 137]:
                logger.info("✅ FortiClient 进程已停止（sudo 免密码）")
                time.sleep(2)
                
                # 将光标移动到屏幕中央
                self.move_cursor_to_center()
                return True
            
            # 如果免密码失败，说明需要密码
            logger.warning(f"⚠️  sudo 返回码 {result.returncode}，尝试不使用 sudo...")
            
            # 尝试不使用 sudo（如果进程是当前用户的）
            result = subprocess.run(
                ['pkill', '-9', '-f', 'forticlient'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            time.sleep(2)
            logger.info("✅ FortiClient 进程已停止")
            
            # 将光标移动到屏幕中央
            self.move_cursor_to_center()
            return True
        
        except Exception as e:
            logger.error(f"停止 FortiClient 失败: {e}")
            return False
    
    def move_cursor_to_center(self):
        """将光标移动到屏幕中央"""
        try:
            # 获取屏幕分辨率
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True,
                text=True,
                env={'DISPLAY': self.display}
            )
            
            # 解析分辨率
            import re
            match = re.search(r'dimensions:\s+(\d+)x(\d+)', result.stdout)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                center_x = width // 2
                center_y = height // 2
                
                logger.info(f"将光标移动到屏幕中央 ({center_x}, {center_y})...")
                subprocess.run(
                    ['xdotool', 'mousemove', str(center_x), str(center_y)],
                    env={'DISPLAY': self.display}
                )
            else:
                # 如果无法获取分辨率，使用默认值（1920x1080 的中央）
                logger.info("将光标移动到屏幕中央 (960, 540)...")
                subprocess.run(
                    ['xdotool', 'mousemove', '960', '540'],
                    env={'DISPLAY': self.display}
                )
        
        except Exception as e:
            logger.debug(f"移动光标失败: {e}")
    
    def start_forticlient(self):
        """启动 FortiClient"""
        logger.info("启动 FortiClient...")
        
        try:
            launch_method = self.config['vpn']['launch_method']
            
            if launch_method == 'gui_click':
                # 通过 GUI 点击启动
                sidebar_x = self.config['vpn']['gui_sidebar_x']
                sidebar_y = self.config['vpn']['gui_sidebar_y']
                
                logger.info(f"点击左边栏图标 ({sidebar_x}, {sidebar_y})...")
                subprocess.run(
                    ['xdotool', 'mousemove', '--sync', str(sidebar_x), str(sidebar_y)],
                    env={'DISPLAY': self.display}
                )
                time.sleep(0.5)
                subprocess.run(
                    ['xdotool', 'click', '1'],
                    env={'DISPLAY': self.display}
                )
                time.sleep(2)
            else:
                logger.error(f"不支持的启动方法: {launch_method}")
                return False
            
            logger.info("✅ 已触发 FortiClient 启动")
            return True
        
        except Exception as e:
            logger.error(f"启动 FortiClient 失败: {e}")
            return False
    
    def click_sidebar_icon(self):
        """点击左边栏图标"""
        try:
            sidebar_x = self.config['vpn']['gui_sidebar_x']
            sidebar_y = self.config['vpn']['gui_sidebar_y']
            
            logger.info(f"点击左边栏图标 ({sidebar_x}, {sidebar_y})...")
            subprocess.run(
                ['xdotool', 'mousemove', '--sync', str(sidebar_x), str(sidebar_y)],
                env={'DISPLAY': self.display}
            )
            time.sleep(0.5)
            subprocess.run(
                ['xdotool', 'click', '1'],
                env={'DISPLAY': self.display}
            )
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"点击左边栏图标失败: {e}")
            return False
    
    def wait_for_window(self):
        """等待窗口出现"""
        window_name = self.config['vpn']['window_name']
        timeout = self.config['reconnect']['window_wait_timeout']
        retry_click_interval = 15  # 每 15 秒重试点击一次
        
        logger.info(f"等待 {window_name} 窗口出现（最多 {timeout} 秒）...")
        
        for i in range(timeout):
            try:
                result = subprocess.run(
                    ['xdotool', 'search', '--name', window_name],
                    capture_output=True,
                    text=True,
                    env={'DISPLAY': self.display}
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    logger.info(f"✅ 窗口已出现（等待 {i+1} 秒）")
                    return True
            
            except Exception:
                pass
            
            # 每 15 秒重试点击一次（可能是密码对话框阻止了启动）
            if i > 0 and i % retry_click_interval == 0:
                logger.warning(f"⚠️  窗口尚未出现，重试点击左边栏图标...")
                self.click_sidebar_icon()
            
            time.sleep(1)
        
        logger.error(f"❌ 窗口未在 {timeout} 秒内出现")
        return False
    
    def resize_window(self):
        """调整窗口大小（已禁用）"""
        # 此功能已禁用，FortiClient 窗口大小不需要调整
        pass
    
    def click_connect_button(self):
        """点击连接按钮（尝试所有驱动）"""
        logger.info("尝试点击连接按钮...")
        
        for driver in self.drivers:
            driver_name = driver.__class__.__name__
            logger.info(f"尝试驱动: {driver_name}")
            
            try:
                if driver.click_connect():
                    logger.info(f"✅ {driver_name} 成功")
                    return True
                else:
                    logger.warning(f"⚠️  {driver_name} 失败")
            
            except Exception as e:
                logger.error(f"❌ {driver_name} 异常: {e}")
        
        logger.error("所有驱动都失败了")
        return False
    
    def wait_for_vpn_connection(self):
        """等待 VPN 连接"""
        timeout = self.config['reconnect']['vpn_connect_timeout']
        check_interval = 10  # 每 10 秒检查一次
        max_checks = timeout // check_interval  # 最多检查次数
        
        logger.info(f"等待 VPN 连接（最多 {timeout} 秒，每 {check_interval} 秒检查一次）...")
        
        for i in range(max_checks):
            time.sleep(check_interval)
            
            logger.info(f"检查 VPN 状态（第 {i+1}/{max_checks} 次）...")
            
            # 方法 1: 使用 forticlient vpn status 命令
            try:
                result = subprocess.run(
                    ['forticlient', 'vpn', 'status'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and 'Status: Connected' in result.stdout:
                    logger.info(f"✅ VPN 已连接（FortiClient 状态），耗时 {(i+1)*check_interval} 秒")
                    return True
            except Exception as e:
                logger.debug(f"forticlient 命令检查失败: {e}")
            
            # 方法 2: 检查网络接口
            try:
                interface = self.config['network']['vpn_interface']
                result = subprocess.run(
                    ['ip', 'addr', 'show', interface],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and 'inet ' in result.stdout:
                    logger.info(f"✅ VPN 已连接（网络接口 {interface}），耗时 {(i+1)*check_interval} 秒")
                    return True
            except Exception as e:
                logger.debug(f"网络接口检查失败: {e}")
            
            logger.debug(f"VPN 尚未连接，继续等待...")
        
        logger.warning(f"⚠️  VPN 在 {timeout} 秒内未连接")
        return False
    
    def minimize_forticlient_window(self):
        """最小化 FortiClient 窗口（已禁用）"""
        # 此功能已禁用，FortiClient 会自动最小化
        pass
