import os
import subprocess

# 定义 GitHub 仓库信息
repo_url = "git@github.com:laityts/result.git"  # 替换为您的仓库 URL
file_name = "cfip.txt"  # 要上传的文件
commit_message = "Add extracted IP addresses"

# 确保文件存在
if not os.path.exists(file_name):
    print(f"文件 {file_name} 不存在，请先生成文件。")
    exit()

# 初始化 Git 仓库（如果尚未初始化）
if not os.path.exists(".git"):
    subprocess.run(["git", "init"], check=True)

# 添加远程仓库（如果尚未添加）
subprocess.run(["git", "remote", "add", "origin", repo_url], check=False)

# 拉取远程仓库内容以同步
subprocess.run(["git", "pull", "origin", "main", "--rebase"], check=False)

# 添加文件到暂存区
subprocess.run(["git", "add", file_name], check=True)

# 提交更改
subprocess.run(["git", "commit", "-m", commit_message], check=True)

# 推送到远程仓库
subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

print(f"文件 {file_name} 已成功上传到 GitHub 仓库 {repo_url}")