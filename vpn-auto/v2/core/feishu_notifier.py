#!/usr/bin/env python3
"""
飞书通知模块
负责发送消息和图片到飞书
"""

import logging
import subprocess
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config
        self.user_id = config['feishu'].get('user_id')
        self.enabled = config['feishu'].get('enabled', False)
        self.openclaw_bin = config['feishu'].get('openclaw_bin', 'openclaw')
        
        if self.enabled:
            if not self.user_id:
                logger.warning("飞书通知已启用，但未配置 user_id")
                self.enabled = False
            else:
                logger.info(f"飞书通知已启用，目标用户: {self.user_id}")
        else:
            logger.info("飞书通知未启用")
    
    def send_text(self, message):
        """发送文本消息"""
        if not self.enabled:
            return False
        
        try:
            # 使用 shell 命令发送消息
            # 转义单引号
            escaped_message = message.replace("'", "'\\''")
            cmd = f"cd ~/openclaw && {self.openclaw_bin} message send --channel feishu --target {self.user_id} --message '{escaped_message}'"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ 飞书消息发送成功")
                return True
            else:
                logger.error(f"❌ 飞书消息发送失败: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"发送飞书消息异常: {e}")
            return False
    
    def send_image(self, image_path, caption=""):
        """发送图片消息"""
        if not self.enabled:
            return False
        
        try:
            # 使用 shell 命令发送图片
            cmd = f"cd ~/openclaw && {self.openclaw_bin} message send --channel feishu --target {self.user_id} --media {image_path}"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ 飞书图片发送成功")
                
                # 如果有说明文字，再发送一条文本消息
                if caption:
                    self.send_text(caption)
                
                return True
            else:
                logger.error(f"❌ 飞书图片发送失败: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"发送飞书图片异常: {e}")
            return False
    
    def take_screenshot_and_send(self, caption=""):
        """截图并发送到飞书"""
        if not self.enabled:
            return False
        
        try:
            # 生成临时截图路径
            screenshot_path = f"/tmp/vpn-saml-{os.getpid()}.png"
            
            # 截图
            logger.info("正在截取屏幕...")
            result = subprocess.run(
                ['scrot', screenshot_path],
                env={'DISPLAY': self.config['system']['display']},
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error("截图失败")
                return False
            
            logger.info(f"截图已保存: {screenshot_path}")
            
            # 发送到飞书
            success = self.send_image(screenshot_path, caption)
            
            # 清理临时文件
            try:
                os.remove(screenshot_path)
            except Exception:
                pass
            
            return success
        
        except Exception as e:
            logger.error(f"截图并发送异常: {e}")
            return False
