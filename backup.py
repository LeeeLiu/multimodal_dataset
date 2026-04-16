#!/usr/bin/env python3


import argparse
import sys
import os


def send_file(file_path, server_url):
    """
    参数:
        file_path: 要发送的本地文件路径
        server_url: 目标服务器URL地址
    """
    try:
        # 导入requests库（需要pip install requests）
        import requests
    except ImportError:
        print("错误: 需要安装requests库")
        print("请运行: pip install requests")
        sys.exit(1)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        sys.exit(1)

    # 获取文件名
    filename = os.path.basename(file_path)

    print(f" 准备发送文件: {file_path}")
    print(f" 目标服务器: {server_url}")
    print(f" 文件大小: {os.path.getsize(file_path)} 字节")

    print("\n" + "=" * 50)
    print("=" * 50)
    
    # 方式1: 使用multipart/form-data上传文件（推荐）
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(server_url, files=files, timeout=30)

        # 检查响应
        if response.status_code == 200:
            print(f"✓ 文件发送成功！")
            print(f"✓ 服务器响应: {response.text}")
        else:
            print(f"✗ 发送失败，状态码: {response.status_code}")
            print(f"✗ 响应内容: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"✗ 发送过程中出现错误: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='文件传输示例脚本'
    )
    parser.add_argument(
        'server_url',
        help='目标服务器URL地址（例如：http://example.com/upload）'
    )
    parser.add_argument(
        'file_path',
        help='要发送的本地文件路径'
    )

    args = parser.parse_args()

    # 调用发送函数
    send_file(args.file_path, args.server_url)


if __name__ == '__main__':
    main()
