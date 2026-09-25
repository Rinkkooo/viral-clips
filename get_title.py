with open(r'C:\Users\user\.gemini\antigravity\brain\aac210ae-2c41-44ce-b283-aabb1233a099\.system_generated\steps\2356\content.md', 'r', encoding='utf-8') as f:
    content = f.read()
import re
m = re.search(r'<title>(.*?)</title>', content)
if m:
    print('Title:', m.group(1))
m2 = re.search(r'title":"([^"]+)"', content)
if m2:
    print('Title2:', m2.group(1))
