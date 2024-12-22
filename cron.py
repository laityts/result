import subprocess
import os

# 设置要添加的定时任务
minute = "00"
hour = "0,12"  # 每12小时执行一次（0点和12点）
day_of_month = "*"
month = "*"
day_of_week = "*"
command = "/data/data/com.termux/files/usr/bin/python3 /data/user/0/com.termux/files/home/result/cfst.py"

# 定义输出日志文件路径
log_file = "/data/user/0/com.termux/files/home/result/cfst.log"

# 定义 Cron 作业的时间表、命令和日志输出
cron_job = f"{minute} {hour} {day_of_month} {month} {day_of_week} {command} >> {log_file} 2>&1"

# 获取当前用户的 Crontab 文件
def get_crontab():
    try:
        # 读取当前用户的 Crontab
        result = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return ""

# 添加新的 Cron 作业
def add_cron_job(cron_job):
    current_crontab = get_crontab()
    
    # 确保 Cron 作业不重复
    if cron_job not in current_crontab:
        # 将新的 Cron 作业添加到 Crontab
        new_crontab = current_crontab + cron_job + "\n"
        subprocess.run(["crontab", "-"], input=new_crontab.encode(), check=True)
        print("Cron job has been added successfully.")
    else:
        print("Cron job already exists.")

# 调用添加 Cron 任务的函数
add_cron_job(cron_job)