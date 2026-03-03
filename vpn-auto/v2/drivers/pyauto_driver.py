#!/usr/bin/env python3
"""
PyAutoGUI 驱动（备用方案）
使用图像识别查找按钮
"""

import logging
import os

logger = logging.getLogger(__name__)


class PyAutoDriver:
    """PyAutoGUI 驱动"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config
        self.display = config['system']['display']
        self.confidence = config['drivers']['pyauto'].get('confidence', 0.8)
        self.button_image = config['drivers']['pyauto'].get('button_image')
        
        # 尝试导入 pyautogui
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.available = True
            logger.info("PyAutoGUI 驱动已加载")
        except ImportError:
            self.pyautogui = None
            self.available = False
            logger.warning("PyAutoGUI 驱动不可用（缺少 pyautogui）")
    
    def click_connect(self):
        """点击连接按钮"""
        if not self.available:
            logger.warning("PyAutoGUI 驱动不可用")
            return False
        
        if not self.button_image or not os.path.exists(self.button_image):
            logger.warning(f"按钮图像不存在: {self.button_image}")
            return False
        
        try:
            logger.info("使用 PyAutoGUI 查找按钮...")
            
            # 设置 DISPLAY
            os.environ['DISPLAY'] = self.display
            
            # 查找按钮
            location = self.pyautogui.locateCenterOnScreen(
                self.button_image,
                confidence=self.confidence
            )
            
            if location:
                logger.info(f"找到按钮: {location}")
                self.pyautogui.click(location)
                logger.info("✅ PyAutoGUI 点击成功")
                return True
            else:
                logger.warning("未找到按钮")
                return False
        
        except Exception as e:
            logger.error(f"PyAutoGUI 驱动异常: {e}")
            return False
