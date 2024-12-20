import os
import subprocess

# 定义 cfst 文件路径
cfst_path = "cfst"

# 检查 cfst 文件是否存在
if not os.path.exists(cfst_path):
    print(f"文件 {cfst_path} 不存在，正在执行安装和测试命令...")

    # 下载 CloudflareST
    subprocess.run(["wget", "-N", "https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_arm64.tar.gz"], check=True)
    
    # 解压缩 tar 文件
    subprocess.run(["tar", "-zxf", "CloudflareST_linux_arm64.tar.gz"], check=True)
    
    # 重命名解压后的文件
    subprocess.run(["mv", "CloudflareST", "cfst"], check=True)
    
    # 设置可执行权限
    subprocess.run(["chmod", "+x", "cfst"], check=True)
    
    # 执行 cfst 命令
    subprocess.run(["./cfst", "-httping", "-tl", "120", "-cfcolo", "HKG", "-sl", "3"], check=True)
else:
    print(f"文件 {cfst_path} 已存在，无需执行安装命令。")