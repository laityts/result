import socket
import re
import time
import os
from datetime import datetime

def ensure_directory_exists(file_path):
    """
    确保文件所在的目录存在，如果不存在则创建
    :param file_path: 文件路径
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def delete_file_if_exists(file_path):
    """
    如果文件存在，则删除文件
    :param file_path: 文件路径
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"已删除旧日志文件: {file_path}")

def extract_ip_port(file_path):
    """
    从文件中提取IP地址和端口
    :param file_path: 文件路径
    :return: 包含 (IP地址, 端口, 原始行内容) 的列表
    """
    ip_port_list = []
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            for line in file:
                # 使用正则表达式提取IP地址和端口
                match = re.match(r"\[?([0-9a-fA-F:.]+)\]?:(\d+)", line)
                if match:
                    ip = match.group(1)  # 提取IP地址
                    port = int(match.group(2))  # 提取端口
                    ip_port_list.append((ip, port, line.strip()))  # 保存IP、端口和原始行
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return ip_port_list

def check_tcp_connectivity(ip_address, port, timeout=3, retries=3):
    """
    通过TCP检测IP地址的指定端口是否连通（支持IPv4和IPv6）
    :param ip_address: 要检测的IP地址
    :param port: 要检测的端口号
    :param timeout: 每次连接的超时时间（秒）
    :param retries: 重试次数
    :return: True（连通）或 False（不连通）
    """
    for attempt in range(retries):
        sock = None
        try:
            # 判断IP地址类型（IPv4或IPv6）
            if ":" in ip_address:  # IPv6
                address_family = socket.AF_INET6
            else:  # IPv4
                address_family = socket.AF_INET
            # 创建socket对象
            sock = socket.socket(address_family, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            # 尝试连接
            print(f"尝试连接 IP地址 {ip_address}:{port} (尝试 {attempt + 1}/{retries})...")
            result = sock.connect_ex((ip_address, port))
            # 如果返回码为0，表示端口连通
            if result == 0:
                print(f"IP地址 {ip_address}:{port} 连通")
                return True
            else:
                print(f"IP地址 {ip_address}:{port} 连接失败，错误码: {result}")
        except Exception as e:
            print(f"检测IP地址 {ip_address} 端口 {port} 时出错（尝试 {attempt + 1}/{retries}）: {e}")
        finally:
            # 关闭socket连接（如果sock已定义）
            if sock:
                sock.close()
        # 等待一段时间后重试
        if attempt < retries - 1:
            time.sleep(1)  # 每次重试前等待1秒
    print(f"IP地址 {ip_address}:{port} 所有尝试均失败")
    return False

def remove_unreachable_ips(file_path, log_path):
    """
    删除文件中不可达的IP地址，并生成日志
    :param file_path: 文件路径
    :param log_path: 日志文件路径
    """
    # 确保目录存在
    ensure_directory_exists(file_path)
    ensure_directory_exists(log_path)

    # 删除旧日志文件（如果存在）
    delete_file_if_exists(log_path)

    # 提取IP地址和端口
    ip_port_list = extract_ip_port(file_path)
    reachable_lines = []  # 保存可达的IP行
    unreachable_ips = []  # 保存不可达的IP地址

    # 检测每个IP地址的端口连通性
    for ip, port, line in ip_port_list:
        print(f"\n开始检测 IP: {ip}, 端口: {port}")
        if check_tcp_connectivity(ip, port):
            reachable_lines.append(line)  # 保存可达的IP行
            print(f"IP: {ip}, 端口: {port} 连通，保留")
        else:
            unreachable_ips.append((ip, port))  # 保存不可达的IP地址
            print(f"IP: {ip}, 端口: {port} 不通，删除")

    # 将可达的IP行写回文件
    with open(file_path, mode="w", encoding="utf-8") as file:
        for line in reachable_lines:
            file.write(line + "\n")

    # 生成日志文件
    with open(log_path, mode="w", encoding="utf-8") as log:
        log.write(f"以下IP地址不通，已从文件中删除（检测时间: {datetime.now()}）：\n")
        for ip, port in unreachable_ips:
            log.write(f"IP: {ip}, 端口: {port}\n")

    print(f"\n日志已保存到 {log_path}")

if __name__ == "__main__":
    file_path = "speed/cfipv6.txt"  # 输入文件
    log_path = "log/sklog.txt"  # 日志文件
    remove_unreachable_ips(file_path, log_path)