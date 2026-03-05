#!/usr/bin/env python3
"""
实时调试 ATSPIDriver
在 FortiClient 窗口打开时运行，详细分析为什么找不到按钮
"""

import os
import sys
import time

os.environ['DISPLAY'] = ':1'
os.environ['QT_ACCESSIBILITY'] = '1'
os.environ['QT_LINUX_ACCESSIBILITY_ALWAYS_ON'] = '1'

try:
    import pyatspi
except ImportError:
    print("❌ 缺少 python3-pyatspi")
    sys.exit(1)


def analyze_node(node, indent=0, max_depth=15):
    """深度分析节点"""
    if indent > max_depth:
        return
    
    prefix = "  " * indent
    
    try:
        # 基本信息
        name = node.name if hasattr(node, 'name') else ""
        role = node.getRole() if hasattr(node, 'getRole') else -1
        role_name = node.getRoleName() if hasattr(node, 'getRoleName') else "unknown"
        
        # 打印节点
        print(f"{prefix}[{role_name}] '{name}'")
        
        # 详细属性
        attrs = []
        
        # 角色编号
        attrs.append(f"role={role}")
        
        # 描述
        if hasattr(node, 'description') and node.description:
            attrs.append(f"desc='{node.description}'")
        
        # 状态
        if hasattr(node, 'getState'):
            try:
                state_set = node.getState()
                states = []
                # 检查常见状态
                if state_set.contains(pyatspi.STATE_ENABLED):
                    states.append("ENABLED")
                if state_set.contains(pyatspi.STATE_VISIBLE):
                    states.append("VISIBLE")
                if state_set.contains(pyatspi.STATE_SHOWING):
                    states.append("SHOWING")
                if state_set.contains(pyatspi.STATE_FOCUSABLE):
                    states.append("FOCUSABLE")
                if state_set.contains(pyatspi.STATE_SENSITIVE):
                    states.append("SENSITIVE")
                if states:
                    attrs.append(f"states={','.join(states)}")
            except:
                pass
        
        # 位置和大小
        if hasattr(node, 'queryComponent'):
            try:
                component = node.queryComponent()
                if component:
                    extents = component.getExtents(pyatspi.DESKTOP_COORDS)
                    if extents.width > 0 and extents.height > 0:
                        attrs.append(f"pos=({extents.x},{extents.y})")
                        attrs.append(f"size={extents.width}x{extents.height}")
            except:
                pass
        
        # 动作
        if hasattr(node, 'queryAction'):
            try:
                action = node.queryAction()
                if action and action.nActions > 0:
                    action_names = []
                    for i in range(action.nActions):
                        action_names.append(action.getName(i))
                    attrs.append(f"actions={','.join(action_names)}")
            except:
                pass
        
        # 文本内容
        if hasattr(node, 'queryText'):
            try:
                text = node.queryText()
                if text:
                    text_content = text.getText(0, -1).strip()
                    if text_content and text_content != '￼':
                        attrs.append(f"text='{text_content[:30]}'")
            except:
                pass
        
        # 打印属性
        if attrs:
            print(f"{prefix}  → {' | '.join(attrs)}")
        
        # 检查是否是按钮
        if role == pyatspi.ROLE_PUSH_BUTTON:
            print(f"{prefix}  ⭐ 这是一个按钮！")
        
        # 检查名称中是否包含关键词
        keywords = ['connect', 'saml', 'login', 'sign', 'auth', 'ok', 'confirm', 'submit']
        if name:
            name_lower = name.lower()
            for keyword in keywords:
                if keyword in name_lower:
                    print(f"{prefix}  🔍 名称包含关键词: {keyword}")
        
        # 递归子节点
        if hasattr(node, 'childCount'):
            child_count = node.childCount
            if child_count > 0:
                for i in range(child_count):
                    try:
                        child = node.getChildAtIndex(i)
                        analyze_node(child, indent + 1, max_depth)
                    except Exception as e:
                        print(f"{prefix}  ⚠️  子节点 {i} 错误: {e}")
    
    except Exception as e:
        print(f"{prefix}⚠️  节点分析错误: {e}")


def search_buttons(node, depth=0, max_depth=15):
    """搜索所有按钮"""
    buttons = []
    
    if depth > max_depth:
        return buttons
    
    try:
        role = node.getRole() if hasattr(node, 'getRole') else -1
        name = node.name if hasattr(node, 'name') else ""
        
        # 检查是否是按钮
        if role == pyatspi.ROLE_PUSH_BUTTON:
            buttons.append({
                'name': name,
                'node': node,
                'depth': depth
            })
        
        # 递归搜索
        if hasattr(node, 'childCount'):
            for i in range(node.childCount):
                try:
                    child = node.getChildAtIndex(i)
                    buttons.extend(search_buttons(child, depth + 1, max_depth))
                except:
                    pass
    
    except:
        pass
    
    return buttons


def main():
    print("=" * 80)
    print("ATSPIDriver 实时调试工具")
    print("=" * 80)
    print()
    
    # 等待 FortiClient 窗口
    print("等待 FortiClient 窗口...")
    for i in range(10):
        try:
            desktop = pyatspi.Registry.getDesktop(0)
            
            for j in range(desktop.childCount):
                try:
                    app = desktop.getChildAtIndex(j)
                    app_name = app.name if hasattr(app, 'name') else ""
                    
                    if 'forti' in app_name.lower():
                        print(f"✅ 找到 FortiClient 应用")
                        print()
                        
                        # 1. 打印完整树结构
                        print("=" * 80)
                        print("完整 UI 树结构")
                        print("=" * 80)
                        print()
                        analyze_node(app)
                        print()
                        
                        # 2. 搜索所有按钮
                        print("=" * 80)
                        print("搜索按钮元素")
                        print("=" * 80)
                        print()
                        
                        buttons = search_buttons(app)
                        
                        if buttons:
                            print(f"✅ 找到 {len(buttons)} 个按钮:")
                            for idx, btn in enumerate(buttons):
                                print(f"  {idx+1}. 名称: '{btn['name']}' (深度: {btn['depth']})")
                        else:
                            print("❌ 未找到任何按钮元素")
                        
                        print()
                        
                        # 3. 分析结论
                        print("=" * 80)
                        print("分析结论")
                        print("=" * 80)
                        print()
                        
                        if not buttons:
                            print("❌ FortiClient 没有暴露任何按钮元素给 AT-SPI")
                            print()
                            print("可能的原因:")
                            print("1. 应用使用自定义渲染（QML、OpenGL、Canvas）")
                            print("2. 应用没有实现 AT-SPI 接口")
                            print("3. 按钮是图像或自绘控件，不是标准 Widget")
                            print()
                            print("验证方法:")
                            print("- 检查应用是否使用 Qt Widgets")
                            print("- 检查应用是否使用 QML")
                            print("- 使用 Accerciser 工具查看 UI 树")
                        else:
                            print("✅ 找到按钮元素，但可能名称不匹配")
                            print()
                            print("建议:")
                            print("- 检查按钮名称是否包含 'connect', 'saml', 'login' 等关键词")
                            print("- 尝试点击找到的按钮")
                        
                        return
                
                except:
                    pass
        
        except Exception as e:
            print(f"⚠️  错误: {e}")
        
        time.sleep(1)
        print(f"  等待中... ({i+1}/10)")
    
    print()
    print("❌ 10 秒内未找到 FortiClient 窗口")


if __name__ == '__main__':
    main()
