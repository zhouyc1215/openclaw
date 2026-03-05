#!/usr/bin/env python3
"""
调试 AT-SPI 驱动
详细输出 FortiClient 的 UI 树结构
"""

import os
import sys

# 设置 DISPLAY
os.environ['DISPLAY'] = ':1'

try:
    import pyatspi
except ImportError:
    print("❌ 缺少 python3-pyatspi")
    sys.exit(1)


def print_tree(node, indent=0, max_depth=5):
    """递归打印 UI 树"""
    if indent > max_depth:
        return
    
    try:
        prefix = "  " * indent
        role_name = node.getRoleName() if hasattr(node, 'getRoleName') else "unknown"
        name = node.name if hasattr(node, 'name') else "no-name"
        
        print(f"{prefix}[{role_name}] {name}")
        
        # 如果是按钮，打印更多信息
        if role_name == "push button":
            print(f"{prefix}  → 这是一个按钮！")
            if hasattr(node, 'getState'):
                state = node.getState()
                print(f"{prefix}  → 状态: {state}")
        
        # 递归打印子节点
        if hasattr(node, 'childCount'):
            for i in range(node.childCount):
                try:
                    child = node.getChildAtIndex(i)
                    print_tree(child, indent + 1, max_depth)
                except Exception as e:
                    print(f"{prefix}  ⚠️  无法访问子节点 {i}: {e}")
    
    except Exception as e:
        print(f"{'  ' * indent}⚠️  节点错误: {e}")


def main():
    print("=" * 60)
    print("AT-SPI 调试工具")
    print("=" * 60)
    
    try:
        # 获取桌面
        desktop = pyatspi.Registry.getDesktop(0)
        print(f"\n✅ 桌面应用数量: {desktop.childCount}\n")
        
        # 遍历所有应用
        found_forti = False
        for i in range(desktop.childCount):
            try:
                app = desktop.getChildAtIndex(i)
                app_name = app.name if hasattr(app, 'name') else "unknown"
                
                # 只关注 FortiClient
                if 'forti' in app_name.lower():
                    found_forti = True
                    print(f"\n{'=' * 60}")
                    print(f"找到 FortiClient 应用: {app_name}")
                    print(f"{'=' * 60}\n")
                    
                    # 打印完整的 UI 树
                    print_tree(app, max_depth=10)
                    
                    print(f"\n{'=' * 60}")
                    print("搜索关键词...")
                    print(f"{'=' * 60}\n")
                    
                    # 搜索特定关键词
                    keywords = ['connect', 'saml', 'login', 'sign', 'auth', 'ok', 'confirm']
                    for keyword in keywords:
                        result = search_keyword(app, keyword)
                        if result:
                            print(f"✅ 找到包含 '{keyword}' 的节点:")
                            for node_info in result:
                                print(f"   - [{node_info['role']}] {node_info['name']}")
            
            except Exception as e:
                print(f"⚠️  无法访问应用 {i}: {e}")
        
        if not found_forti:
            print("\n❌ 未找到 FortiClient 应用")
            print("\n所有应用列表:")
            for i in range(desktop.childCount):
                try:
                    app = desktop.getChildAtIndex(i)
                    print(f"  - {app.name}")
                except:
                    pass
    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def search_keyword(node, keyword, results=None, depth=0, max_depth=10):
    """搜索包含关键词的节点"""
    if results is None:
        results = []
    
    if depth > max_depth:
        return results
    
    try:
        name = node.name if hasattr(node, 'name') else ""
        role_name = node.getRoleName() if hasattr(node, 'getRoleName') else "unknown"
        
        if name and keyword.lower() in name.lower():
            results.append({
                'name': name,
                'role': role_name,
                'node': node
            })
        
        # 递归搜索子节点
        if hasattr(node, 'childCount'):
            for i in range(node.childCount):
                try:
                    child = node.getChildAtIndex(i)
                    search_keyword(child, keyword, results, depth + 1, max_depth)
                except:
                    pass
    
    except:
        pass
    
    return results


if __name__ == '__main__':
    main()
