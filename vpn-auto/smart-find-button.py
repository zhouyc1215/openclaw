#!/usr/bin/env python3
"""
智能查找 SAML Login 按钮
策略：
1. 查找深蓝色区域
2. 过滤掉太小或太大的区域
3. 选择最接近屏幕中心的按钮大小的区域
4. Hover + Click
"""

import cv2
import numpy as np
import os
import time
import subprocess

# 配置
SCREENSHOT = "screen.png"
DISPLAY = ":1"

# 深蓝色的 HSV 范围（FortiClient 按钮的蓝色）
BLUE_LOWER = np.array([100, 100, 100])
BLUE_UPPER = np.array([130, 255, 255])

# 按钮尺寸范围（根据之前的观察）
MIN_BUTTON_AREA = 2000   # 最小面积
MAX_BUTTON_AREA = 50000  # 最大面积
MIN_BUTTON_WIDTH = 80    # 最小宽度
MAX_BUTTON_WIDTH = 300   # 最大宽度
MIN_BUTTON_HEIGHT = 25   # 最小高度
MAX_BUTTON_HEIGHT = 80   # 最大高度

def log(message):
    """打印日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def take_screenshot():
    """使用 scrot 截图"""
    os.environ['DISPLAY'] = DISPLAY
    result = subprocess.run(["scrot", SCREENSHOT], capture_output=True)
    if result.returncode == 0:
        log(f"✅ 截图已保存: {SCREENSHOT}")
        return True
    else:
        log(f"❌ 截图失败")
        return False

def find_button_candidates(img):
    """查找所有可能的按钮候选"""
    log("查找深蓝色区域...")
    
    # 转换到 HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 创建蓝色掩码
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    
    # 形态学操作
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 保存掩码
    cv2.imwrite("blue_mask_debug.png", mask)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        log(f"❌ 未找到蓝色区域")
        return []
    
    log(f"找到 {len(contours)} 个蓝色区域")
    
    # 过滤候选
    candidates = []
    
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        
        # 检查尺寸是否符合按钮特征
        if (MIN_BUTTON_AREA <= area <= MAX_BUTTON_AREA and
            MIN_BUTTON_WIDTH <= w <= MAX_BUTTON_WIDTH and
            MIN_BUTTON_HEIGHT <= h <= MAX_BUTTON_HEIGHT):
            
            center_x = x + w // 2
            center_y = y + h // 2
            
            # 计算到屏幕中心的距离
            screen_center_x = img.shape[1] // 2
            screen_center_y = img.shape[0] // 2
            distance = np.sqrt((center_x - screen_center_x)**2 + 
                             (center_y - screen_center_y)**2)
            
            candidates.append({
                'index': i,
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'area': area,
                'center_x': center_x,
                'center_y': center_y,
                'distance': distance
            })
            
            log(f"  候选 {i}: 位置=({x},{y}), 尺寸={w}x{h}, 面积={area}, 距中心={distance:.0f}px")
    
    # 按距离排序（最接近中心的优先）
    candidates.sort(key=lambda c: c['distance'])
    
    return candidates

def wait_for_forticlient(max_wait=30):
    """等待 FortiClient 窗口出现"""
    log("等待 FortiClient 窗口出现...")
    
    for i in range(max_wait):
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", "FortiClient"],
                capture_output=True,
                text=True,
                env={"DISPLAY": DISPLAY}
            )
            
            if result.returncode == 0 and result.stdout.strip():
                log(f"✅ FortiClient 窗口已出现（等待 {i+1} 秒）")
                return True
        except Exception:
            pass
        
        if i < max_wait - 1:
            time.sleep(1)
    
    log(f"❌ FortiClient 窗口出现超时（{max_wait} 秒）")
    return False

def wait_for_gui_ready(wait_time=10):
    """等待 GUI 界面完全加载"""
    log(f"等待 GUI 界面完全加载（{wait_time} 秒）...")
    time.sleep(wait_time)
    log(f"✅ GUI 界面应该已完全加载")
    return True

def resize_and_position_window():
    """调整窗口大小和位置"""
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip().split('\n')[0]
            log(f"调整窗口 {window_id} 的大小和位置...")
            
            # 移动窗口到可见位置
            subprocess.run(
                ["xdotool", "windowmove", window_id, "100", "100"],
                env={"DISPLAY": DISPLAY}
            )
            time.sleep(0.3)
            
            # 调整窗口大小
            subprocess.run(
                ["xdotool", "windowsize", window_id, "1200", "800"],
                env={"DISPLAY": DISPLAY}
            )
            time.sleep(0.3)
            
            log(f"✅ 窗口已调整为 1200x800，位置 (100, 100)")
            return True
    except Exception as e:
        log(f"⚠️  调整窗口失败: {e}")
    
    return False

def activate_window():
    """激活 FortiClient 窗口"""
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip().split('\n')[0]
            log(f"找到窗口 ID: {window_id}")
            
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", window_id],
                env={"DISPLAY": DISPLAY}
            )
            time.sleep(0.5)
            log(f"✅ 窗口已激活")
            return True
    except Exception as e:
        log(f"⚠️  激活窗口失败: {e}")
    
    return False

def verify_cursor_position(target_x, target_y):
    """验证光标是否在目标位置"""
    try:
        result = subprocess.run(
            ["xdotool", "getmouselocation", "--shell"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        
        if result.returncode == 0:
            output = result.stdout
            x = int([line for line in output.split('\n') if line.startswith('X=')][0].split('=')[1])
            y = int([line for line in output.split('\n') if line.startswith('Y=')][0].split('=')[1])
            
            distance = np.sqrt((x - target_x)**2 + (y - target_y)**2)
            log(f"  当前光标位置: ({x}, {y}), 距离目标: {distance:.1f}px")
            
            return distance < 5  # 允许5像素误差
    except Exception as e:
        log(f"  ⚠️  无法验证光标位置: {e}")
    
    return False

def hover_and_click(x, y):
    """移动光标到按钮中央（触发 hover 效果）然后点击并按 Enter"""
    os.environ['DISPLAY'] = DISPLAY
    
    # 移动到按钮中央
    log(f"移动光标到按钮中央 ({x}, {y})...")
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], 
                   env={"DISPLAY": DISPLAY})
    
    # 验证光标位置
    log(f"验证光标位置...")
    if not verify_cursor_position(x, y):
        log(f"⚠️  光标位置不准确，重新移动...")
        subprocess.run(["xdotool", "mousemove", str(x), str(y)], 
                       env={"DISPLAY": DISPLAY})
        time.sleep(0.2)
        verify_cursor_position(x, y)
    
    # 停留1秒（等待 hover 效果）
    log(f"停留1秒，等待 hover 效果...")
    time.sleep(1.0)
    
    # 截图验证 hover 效果
    log(f"截图验证 hover 效果...")
    subprocess.run(["scrot", "hover_effect.png"], 
                   env={"DISPLAY": DISPLAY}, 
                   capture_output=True)
    log(f"  hover 效果截图已保存: hover_effect.png")
    
    # 点击鼠标（单击）
    log(f"点击鼠标...")
    subprocess.run(["xdotool", "click", "1"], 
                   env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    
    # 按 Enter 键确认
    log(f"按 Enter 键确认...")
    subprocess.run(["xdotool", "key", "Return"], 
                   env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    
    log(f"✅ 已点击坐标 ({x}, {y}) 并按 Enter 键")

def save_debug_image(img, candidates, selected):
    """保存调试图像"""
    debug_img = img.copy()
    
    # 标记所有候选
    for candidate in candidates:
        x = candidate['x']
        y = candidate['y']
        w = candidate['w']
        h = candidate['h']
        
        # 非选中的用绿色
        color = (0, 255, 0) if candidate != selected else (255, 0, 0)
        thickness = 2 if candidate != selected else 3
        
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), color, thickness)
        
        # 标记索引
        cv2.putText(debug_img, f"#{candidate['index']}", (x, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # 标记选中的按钮
    if selected:
        cx = selected['center_x']
        cy = selected['center_y']
        cv2.circle(debug_img, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(debug_img, "SELECTED", (selected['x'], selected['y']-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    cv2.imwrite("button_candidates.png", debug_img)
    log(f"✅ 调试图像已保存: button_candidates.png")

def main():
    """主函数"""
    log("=" * 60)
    log("智能查找 SAML Login 按钮")
    log("=" * 60)
    log("")
    
    # 0. 等待 FortiClient 窗口出现
    log("步骤 0: 等待 FortiClient 窗口出现...")
    if not wait_for_forticlient(max_wait=30):
        log("")
        log("提示：")
        log("  1. 检查 FortiClient 是否正在启动")
        log("  2. 手动启动 FortiClient GUI")
        log("  3. 增加等待时间")
        return False
    log("")
    
    # 0.5. 等待 GUI 界面完全加载
    log("步骤 0.5: 等待 GUI 界面完全加载...")
    wait_for_gui_ready(wait_time=10)
    log("")
    
    # 0.6. 调整窗口大小和位置
    log("步骤 0.6: 调整窗口大小和位置...")
    resize_and_position_window()
    log("")
    
    # 1. 激活窗口
    log("步骤 1: 激活 FortiClient 窗口...")
    activate_window()
    log("")
    
    # 2. 截图
    log("步骤 2: 截取屏幕...")
    if not take_screenshot():
        return False
    log("")
    
    # 3. 读取图像
    img = cv2.imread(SCREENSHOT)
    if img is None:
        log(f"❌ 无法读取截图")
        return False
    
    log(f"屏幕尺寸: {img.shape[1]}x{img.shape[0]}")
    log("")
    
    # 4. 查找候选按钮
    log("步骤 3: 查找按钮候选...")
    candidates = find_button_candidates(img)
    
    if not candidates:
        log(f"❌ 未找到符合条件的按钮")
        log("")
        log("提示：")
        log("  1. 检查 FortiClient 窗口是否打开")
        log("  2. 检查 SAML Login 按钮是否可见")
        log("  3. 查看 blue_mask_debug.png 确认颜色检测")
        log("  4. GUI 可能还没有完全加载，尝试增加等待时间")
        return False
    
    log(f"✅ 找到 {len(candidates)} 个候选")
    log("")
    
    # 5. 选择最佳候选（最接近中心的）
    selected = candidates[0]
    log(f"选择候选 #{selected['index']} (最接近屏幕中心)")
    log(f"  位置: ({selected['x']}, {selected['y']})")
    log(f"  尺寸: {selected['w']}x{selected['h']}")
    log(f"  中心: ({selected['center_x']}, {selected['center_y']})")
    log("")
    
    # 6. 保存调试图像
    save_debug_image(img, candidates, selected)
    log("")
    
    # 7. Hover + Click + Enter
    log("步骤 4: 移动光标、点击按钮并按 Enter...")
    hover_and_click(selected['center_x'], selected['center_y'])
    log("")
    
    log("=" * 60)
    log("✅ 操作完成")
    log("=" * 60)
    log("")
    log("请检查 VPN 是否开始连接")
    log("调试文件:")
    log("  - blue_mask_debug.png (蓝色掩码)")
    log("  - button_candidates.png (候选按钮)")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
