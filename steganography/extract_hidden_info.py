#!/usr/bin/env python3
"""
从MP3文件的ID3v2元数据中提取隐藏的文本
"""
import struct

def extract_from_id3v2(file_path):
    """从ID3v2标签中提取文本"""
    print(f"\n正在从文件提取: {file_path}")
    print("-" * 60)

    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        # 检查ID3v2标签
        if data[:3] != b'ID3':
            print("❌ 没有找到ID3v2标签")
            return None

        # 解析标签大小（同步安全整数）
        size_bytes = data[6:10]
        tag_size = (size_bytes[0] << 21) | (size_bytes[1] << 14) | \
                   (size_bytes[2] << 7) | size_bytes[3]

        print(f"✅ 检测到ID3v2标签，大小: {tag_size} 字节")

        extracted = []
        pos = 10  # 跳过ID3v2头部

        while pos < 10 + tag_size:
            # 读取帧ID
            frame_id = data[pos:pos+4]
            if frame_id[0] == 0:  # 填充字节
                break

            # 读取帧大小
            frame_size = struct.unpack('>I', data[pos+4:pos+8])[0]

            # 读取帧数据
            frame_data = data[pos+10:pos+10+frame_size]

            if frame_id == b'TXXX':
                # TXXX: 自定义文本字段
                encoding = frame_data[0]
                desc_end = frame_data.find(b'\x00', 1)
                text_start = desc_end + 1
                text = frame_data[text_start:].decode('utf-8')
                desc = frame_data[1:desc_end].decode('utf-8')
                print(f"\n✅ TXXX帧 - 描述: {desc}")
                print(f"   内容: {text}")
                extracted.append(text)

            elif frame_id == b'COMM':
                # COMM: 注释字段
                encoding = frame_data[0]
                lang = frame_data[1:4].decode('ascii')
                desc_end = frame_data.find(b'\x00', 4)
                text_start = desc_end + 1 if desc_end != -1 else 4
                text = frame_data[text_start:].decode('utf-8')
                print(f"\n✅ COMM帧 - 语言: {lang}")
                print(f"   内容: {text}")
                extracted.append(text)

            # 移动到下一个帧
            pos += 10 + frame_size

        return extracted if extracted else None

    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("MP3隐写文本提取工具")
    print("=" * 60)

    mp3_file = "hidden_message.mp3"

    # 提取隐藏文本
    result = extract_from_id3v2(mp3_file)

