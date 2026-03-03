#!/usr/bin/env python3
"""
OpenCV 视觉驱动（兜底方案）
使用颜色检测识别按钮
"""

import logging
import subprocess
import time
import os

logger = logging.getLogger(__name__)


class VisionDriver:
    """OpenCV 视觉驱动"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config
        self.display = config['system']['display']
        self.screenshot_path = config['system']['screenshot_path']
        self.debug_output = config['drivers']['vision'].get('debug_output', False)
        
        # 尝试导入 OpenCV
        try:
            import cv2
            import numpy as np
            self.cv2 = cv2
            self.np = np
            self.available = True
            logger.info("OpenCV 驱动已加载")
        except ImportError:
            self.cv2 = None
            self.np = None
            self.available = False
            logger.warning("OpenCV 驱动不可用（缺少 opencv-python）")
    
    def click_connect(self):
        """点击连接按钮"""
        if not self.available:
            logger.warning("OpenCV 驱动不可用")
            return False
        
        try:
            logger.info("使用 OpenCV 查找按钮...")
            
            # 1. 截图
            if not self._take_screenshot():
                logger.error("截图失败")
                return False
            
            # 2. 查找按钮
            button = self._find_button()
            if not button:
                logger.warning("未找到按钮")
                return False
            
            logger.info(f"找到按钮: ({button['center_x']}, {button['center_y']})")
            
            # 3. 点击按钮
            self._click_button(button['center_x'], button['center_y'])
            logger.info("✅ OpenCV 点击成功")
            return True
        
        except Exception as e:
            logger.error(f"OpenCV 驱动异常: {e}")
            return False
    
    def _take_screenshot(self):
        """截图"""
        try:
            os.environ['DISPLAY'] = self.display
            result = subprocess.run(
                ['scrot', self.screenshot_path],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False
    
    def _find_button(self):
        """查找按钮"""
        try:
            # 读取截图
            img = self.cv2.imread(self.screenshot_path)
            if img is None:
                logger.error("无法读取截图")
                return None
            
            # 颜色空间转换
            hsv = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2HSV)
            
            # 颜色范围筛选
            hsv_lower = self.np.array(self.config['button']['hsv_lower'])
            hsv_upper = self.np.array(self.config['button']['hsv_upper'])
            mask = self.cv2.inRange(hsv, hsv_lower, hsv_upper)
            
            # 形态学处理
            kernel = self.np.ones((5, 5), self.np.uint8)
            mask = self.cv2.morphologyEx(mask, self.cv2.MORPH_CLOSE, kernel)
            mask = self.cv2.morphologyEx(mask, self.cv2.MORPH_OPEN, kernel)
            
            # 轮廓检测
            contours, _ = self.cv2.findContours(
                mask,
                self.cv2.RETR_EXTERNAL,
                self.cv2.CHAIN_APPROX_SIMPLE
            )
            
            # 候选筛选
            candidates = []
            screen_center_x = img.shape[1] // 2
            screen_center_y = img.shape[0] // 2
            
            for contour in contours:
                area = self.cv2.contourArea(contour)
                x, y, w, h = self.cv2.boundingRect(contour)
                
                # 尺寸约束
                if (self.config['button']['min_area'] <= area <= self.config['button']['max_area'] and
                    self.config['button']['min_width'] <= w <= self.config['button']['max_width'] and
                    self.config['button']['min_height'] <= h <= self.config['button']['max_height']):
                    
                    center_x = x + w // 2
                    center_y = y + h // 2
                    distance = self.np.sqrt(
                        (center_x - screen_center_x)**2 +
                        (center_y - screen_center_y)**2
                    )
                    
                    candidates.append({
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'center_x': center_x,
                        'center_y': center_y,
                        'distance': distance
                    })
            
            # 选择最接近屏幕中心的候选
            if candidates:
                candidates.sort(key=lambda c: c['distance'])
                return candidates[0]
            
            return None
        
        except Exception as e:
            logger.error(f"查找按钮失败: {e}")
            return None
    
    def _click_button(self, x, y):
        """点击按钮"""
        try:
            os.environ['DISPLAY'] = self.display
            
            # 移动光标
            subprocess.run(
                ['xdotool', 'mousemove', '--sync', str(x), str(y)],
                env={'DISPLAY': self.display}
            )
            time.sleep(1.0)
            
            # 点击
            subprocess.run(
                ['xdotool', 'click', '1'],
                env={'DISPLAY': self.display}
            )
            time.sleep(0.5)
            
            # 按 Enter
            subprocess.run(
                ['xdotool', 'key', 'Return'],
                env={'DISPLAY': self.display}
            )
            time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"点击按钮失败: {e}")
