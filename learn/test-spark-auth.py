#!/usr/bin/env python3
import base64

# 你提供的凭证
app_id = "6b26f509"
api_key = "c39ec6572d2e0f35cffa00e81f9a7ae5"
api_secret = "OWU5MWFjNWZmNWM5NDJkMDE0ZWYzZWE2"

print("=== 星火 API 凭证检查 ===")
print(f"AppID: {app_id}")
print(f"APIKey: {api_key}")
print(f"APISecret: {api_secret}")
print(f"APISecret 长度: {len(api_secret)}")

# 尝试 base64 解码 APISecret（有些平台会 base64 编码）
try:
    decoded = base64.b64decode(api_secret).decode('utf-8')
    print(f"APISecret (base64 decoded): {decoded}")
except:
    print("APISecret 不是 base64 编码")

print("\n请确认：")
print("1. AppID 是否正确？")
print("2. 该 AppID 是否已开通星火 v3.5 服务？")
print("3. APISecret 是否完整？（应该是32位字符）")
