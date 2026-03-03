#!/usr/bin/env python3
"""
AT-SPI 驱动（主方案）
使用 Linux 无障碍技术直接访问 UI 元素，无需截图
"""

import logging

logger = logging.getLogger(__name__)


class ATSPIDriver:
    """AT-SPI 驱动"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config
        self.timeout = config['drivers']['atspi'].get('timeout', 10)
        
        # 尝试导入 pyatspi
        try:
            import pyatspi
            self.pyatspi = pyatspi
            self.available = True
            logger.info("AT-SPI 驱动已加载")
        except ImportError:
            self.pyatspi = None
            self.available = False
            logger.warning("AT-SPI 驱动不可用（缺少 python3-pyatspi）")
    
    def click_connect(self):
        """点击连接按钮"""
        if not self.available:
            logger.warning("AT-SPI 驱动不可用")
            return False
        
        try:
            logger.info("使用 AT-SPI 查找按钮...")
            
            # 获取桌面
            desktop = self.pyatspi.Registry.getDesktop(0)
            
            # 遍历所有应用
            for app in desktop:
                if 'forti' in app.name.lower():
                    logger.info(f"找到应用: {app.name}")
                    
                    # 查找连接按钮
                    button = self._find_button(app, 'connect')
                    if not button:
                        button = self._find_button(app, 'saml')
                    if not button:
                        button = self._find_button(app, 'login')
                    
                    if button:
                        logger.info(f"找到按钮: {button.name}")
                        button.doAction(0)  # 执行默认动作（点击）
                        logger.info("✅ AT-SPI 点击成功")
                        return True
            
            logger.warning("未找到 FortiClient 应用或按钮")
            return False
        
        except Exception as e:
            logger.error(f"AT-SPI 驱动异常: {e}")
            return False
    
    def _find_button(self, node, keyword):
        """递归查找按钮"""
        try:
            # 检查当前节点
            if node.name and keyword.lower() in node.name.lower():
                # 检查是否是按钮
                if node.getRole() == self.pyatspi.ROLE_PUSH_BUTTON:
                    return node
            
            # 递归查找子节点
            for i in range(node.childCount):
                child = node.getChildAtIndex(i)
                result = self._find_button(child, keyword)
                if result:
                    return result
        
        except Exception:
            pass
        
        return None
