#!/usr/bin/env python3
"""
详细调试 AT-SPI - 显示所有属性和状态
"""

import os
import sys

os.environ['DISPLAY'] = ':1'
os.environ['QT_ACCESSIBILITY'] = '1'
os.environ['QT_LINUX_ACCESSIBILITY_ALWAYS_ON'] = '1'

try:
    import pyatspi
except ImportError:
    print("❌ 缺少 python3-pyatspi")
    sys.exit(1)


def print_node_details(node, indent=0):
    """打印节点的详细信息"""
    prefix = "  " * indent
    
    try:
        # 基本信息
        name = node.name if hasattr(node, 'name') else "no-name"
        role_name = node.getRoleName() if hasattr(node, 'getRoleName') else "unknown"
        
        print(f"{prefix}[{role_name}] {name}")
        
        # 详细属性
        if hasattr(node, 'description') and node.description:
            print(f"{prefix}  描述: {node.description}")
        
        if hasattr(node, 'getState'):
            try:
                state_set = node.getState()
                states = []
                for i in range(64):
                    if state_set.contains(i):
                        state_name = pyatspi.stateToString(i)
                        states.append(state_name)
                if states:
                    print(f"{prefix}  状态: {', '.join(states)}")
            except:
                pass
        
        # 动作
        if hasattr(node, 'queryAction'):
            try:
                action = node.queryAction()
                if action:
                    n_actions = action.nActions
                    if n_actions > 0:
                        print(f"{prefix}  动作数量: {n_actions}")
                        for i in range(n_actions):
                            action_name = action.getName(i)
                            print(f"{prefix}    动作 {i}: {action_name}")
            except:
                pass
        
        # 文本
        if hasattr(node, 'queryText'):
            try:
                text = node.queryText()
                if text:
                    text_content = text.getText(0, -1)
                    if text_content:
                        print(f"{prefix}  文本: {text_content[:50]}")
            except:
                pass
        
        # 递归子节点
        if hasattr(node, 'childCount'):
            child_count = node.childCount
            if child_count > 0:
                print(f"{prefix}  子节点数量: {child_count}")
                for i in range(min(child_count, 20)):  # 限制最多20个子节点
                    try:
                        child = node.getChildAtIndex(i)
                        print_node_details(child, indent + 1)
                    except Exception as e:
                        print(f"{prefix}  ⚠️  无法访问子节点 {i}: {e}")
    
    except Exception as e:
        print(f"{prefix}⚠️  节点错误: {e}")


def main():
    print("=" * 80)
    print("AT-SPI 详细调试工具")
    print("=" * 80)
    print()
    print("环境变量:")
    print(f"  DISPLAY: {os.environ.get('DISPLAY')}")
    print(f"  QT_ACCESSIBILITY: {os.environ.get('QT_ACCESSIBILITY')}")
    print(f"  QT_LINUX_ACCESSIBILITY_ALWAYS_ON: {os.environ.get('QT_LINUX_ACCESSIBILITY_ALWAYS_ON')}")
    print()
    
    try:
        desktop = pyatspi.Registry.getDesktop(0)
        print(f"桌面应用数量: {desktop.childCount}")
        print()
        
        # 查找 FortiClient
        for i in range(desktop.childCount):
            try:
                app = desktop.getChildAtIndex(i)
                app_name = app.name if hasattr(app, 'name') else "unknown"
                
                if 'forti' in app_name.lower():
                    print("=" * 80)
                    print(f"找到 FortiClient 应用: {app_name}")
                    print("=" * 80)
                    print()
                    
                    # 打印完整的树结构和详细信息
                    print_node_details(app)
                    
                    print()
                    print("=" * 80)
                    print("分析结论")
                    print("=" * 80)
                    print()
                    
                    # 检查是否有可交互的元素
                    has_buttons = False
                    has_actions = False
                    
                    def check_interactive(node, depth=0):
                        nonlocal has_buttons, has_actions
                        if depth > 10:
                            return
                        
                        try:
                            role_name = node.getRoleName() if hasattr(node, 'getRoleName') else ""
                            if 'button' in role_name.lower():
                                has_buttons = True
                            
                            if hasattr(node, 'queryAction'):
                                try:
                                    action = node.queryAction()
                                    if action and action.nActions > 0:
                                        has_actions = True
                                except:
                                    pass
                            
                            if hasattr(node, 'childCount'):
                                for i in range(node.childCount):
                                    try:
                                        child = node.getChildAtIndex(i)
                                        check_interactive(child, depth + 1)
                                    except:
                                        pass
                        except:
                            pass
                    
                    check_interactive(app)
                    
                    if has_buttons:
                        print("✅ 找到按钮元素")
                    else:
                        print("❌ 未找到按钮元素")
                    
                    if has_actions:
                        print("✅ 找到可执行动作")
                    else:
                        print("❌ 未找到可执行动作")
                    
                    print()
                    
                    if not has_buttons and not has_actions:
                        print("结论: FortiClient 的 UI 元素未暴露给 AT-SPI")
                        print()
                        print("可能原因:")
                        print("1. FortiClient 是 Qt 应用，但未启用 AT-SPI 支持")
                        print("2. 应用使用了自定义渲染，绕过了标准 UI 框架")
                        print("3. 需要在 FortiClient 启动时设置环境变量")
                        print()
                        print("建议:")
                        print("- 使用 PyAutoDriver（图像识别）")
                        print("- 使用 VisionDriver（颜色+形状识别）")
                        print("- ATSPIDriver 不适用于此应用")
            
            except Exception as e:
                pass
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
