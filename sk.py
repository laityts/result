import socket

def check_port_connectivity(ip_address, port, timeout=3):
    """
    检测IP地址的指定端口是否连通
    :param ip_address: 要检测的IP地址
    :param port: 要检测的端口号
    :param timeout: 连接超时时间（秒）
    :return: True（连通）或 False（不连通）
    """
    sock = None  # 初始化sock变量
    try:
        # 创建socket对象
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        # 尝试连接
        result = sock.connect_ex((ip_address, port))
        # 如果返回码为0，表示端口连通
        if result == 0:
            return True
    except Exception as e:
        print(f"检测IP {ip_address} 端口 {port} 时出错: {e}")
    finally:
        # 关闭socket连接（如果sock已定义）
        if sock:
            sock.close()
    return False

# 示例
ip = "104.19.147.87"
port = 443  # 检测HTTPS端口
if check_port_connectivity(ip, port):
    print(f"IP {ip} 的端口 {port} 连通")
else:
    print(f"IP {ip} 的端口 {port} 不连通")