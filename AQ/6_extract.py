#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP3 元数据隐写演示脚本
功能：
  1. 生成一个最小有效的静音 MP3 文件
  2. 将 sample.txt 的文本内容嵌入 MP3 的 ID3 标签（文件头）和 APEv2 标签（文件尾）
  3. 对 MP3 进行 ZIP 压缩，再解压，验证元数据是否完整保留
  4. 打印提取结果与原始文本的对比

保留文件说明：
  - sample.txt          : 原始文本文件
  - embedded.mp3        : 嵌入元数据后的 MP3 文件
  - extract_metadata.py : 本脚本（用于提取信息）
"""

import os
import sys
import zipfile
import hashlib

# ── 依赖检查 ──────────────────────────────────────────────────────────────────
try:
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, COMM, TXXX
    from mutagen.mp3 import MP3
    from mutagen.apev2 import APEv2
except ImportError:
    sys.exit("[错误] 请先安装 mutagen：pip3 install mutagen")

# ── 路径配置 ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
TXT_PATH    = os.path.join(BASE_DIR, "sample.txt")
MP3_PATH    = os.path.join(BASE_DIR, "embedded.mp3")
ZIP_PATH    = os.path.join(BASE_DIR, "embedded_compressed.zip")
UNZIP_DIR   = os.path.join(BASE_DIR, "unzipped_tmp")
UNZIP_MP3   = os.path.join(UNZIP_DIR, "embedded.mp3")

# ── ID3 / APEv2 字段键名 ──────────────────────────────────────────────────────
ID3_TITLE_KEY   = "TIT2"          # ID3 标题字段（文件头）
ID3_COMMENT_KEY = "COMM::zho"     # ID3 注释字段（文件头）
ID3_TXXX_KEY    = "TXXX:hidden"   # ID3 自定义文本字段（文件头）
APE_KEY         = "HiddenPayload" # APEv2 自定义字段（文件尾）

# ─────────────────────────────────────────────────────────────────────────────
# 步骤 1：生成最小静音 MP3（若 embedded.mp3 不存在）
# ─────────────────────────────────────────────────────────────────────────────
def create_silent_mp3(path: str):
    """
    写入一个合法的 MPEG1 Layer3 静音帧。
    帧头 0xFFFB9000 = MPEG1, Layer3, 128kbps, 44100Hz, Stereo, 无填充。
    320 字节的零负载对应一帧静音音频数据。
    """
    # MPEG1 Layer3 帧头（128kbps, 44100Hz, Joint Stereo）
    frame_header = bytes([0xFF, 0xFB, 0x90, 0x00])
    # 128kbps @ 44100Hz 每帧 = 417 字节（含4字节帧头）
    frame_data   = frame_header + bytes(413)
    # 写入 10 帧，约 0.26 秒静音
    with open(path, "wb") as f:
        for _ in range(10):
            f.write(frame_data)
    print(f"[1] 已生成静音 MP3：{path}  ({os.path.getsize(path)} 字节)")


# ─────────────────────────────────────────────────────────────────────────────
# 步骤 2：将文本嵌入 MP3 元数据
# ─────────────────────────────────────────────────────────────────────────────
def embed_text_into_mp3(mp3_path: str, text: str):
    """
    同时写入两种标签：
      • ID3v2（文件头）：TIT2 / COMM / TXXX 三个字段
      • APEv2（文件尾）：自定义 HiddenPayload 字段
    """
    # —— ID3v2 标签（文件头） ——
    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        tags = ID3()

    tags.add(TIT2(encoding=3, text=["embedded_demo"]))
    tags.add(COMM(encoding=3, lang="zho", desc="", text=[text]))
    tags.add(TXXX(encoding=3, desc="hidden", text=[text]))
    tags.save(mp3_path, v2_version=3)
    print("[2] ID3v2 标签（文件头）写入完成")

    # —— APEv2 标签（文件尾） ——
    try:
        ape = APEv2(mp3_path)
    except Exception:
        ape = APEv2()

    ape[APE_KEY] = text
    ape.save(mp3_path)
    print("[2] APEv2 标签（文件尾）写入完成")
    print(f"    嵌入后文件大小：{os.path.getsize(mp3_path)} 字节")


# ─────────────────────────────────────────────────────────────────────────────
# 步骤 3：ZIP 压缩 → 解压
# ─────────────────────────────────────────────────────────────────────────────
def compress_and_decompress(mp3_path: str, zip_path: str, unzip_dir: str) -> str:
    # 压缩
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(mp3_path, arcname=os.path.basename(mp3_path))
    print(f"[3] 压缩完成：{zip_path}  ({os.path.getsize(zip_path)} 字节)")

    # 解压
    os.makedirs(unzip_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(unzip_dir)
    unzipped_mp3 = os.path.join(unzip_dir, os.path.basename(mp3_path))
    print(f"[3] 解压完成：{unzipped_mp3}  ({os.path.getsize(unzipped_mp3)} 字节)")
    return unzipped_mp3


# ─────────────────────────────────────────────────────────────────────────────
# 步骤 4：从 MP3 提取元数据
# ─────────────────────────────────────────────────────────────────────────────
def extract_text_from_mp3(mp3_path: str) -> dict:
    results = {}

    # —— 读取 ID3v2 ——
    try:
        tags = ID3(mp3_path)
        comm = tags.get(ID3_COMMENT_KEY)
        txxx = tags.get(ID3_TXXX_KEY)
        results["ID3_COMM"]  = str(comm.text[0]) if comm else None
        results["ID3_TXXX"]  = str(txxx.text[0]) if txxx else None
    except Exception as e:
        results["ID3_error"] = str(e)

    # —— 读取 APEv2 ——
    try:
        ape = APEv2(mp3_path)
        results["APEv2"] = str(ape[APE_KEY])
    except Exception as e:
        results["APEv2_error"] = str(e)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 步骤 5：对比验证
# ─────────────────────────────────────────────────────────────────────────────
def verify(original_text: str, extracted: dict):
    print("\n" + "="*60)
    print("  验证结果")
    print("="*60)

    orig_hash = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
    print(f"\n原始文本 SHA-256：{orig_hash}")
    print(f"原始文本内容：\n{repr(original_text)}\n")

    all_pass = True
    for field, value in extracted.items():
        if "error" in field.lower():
            print(f"[WARN] {field}: {value}")
            continue
        if value is None:
            print(f"[FAIL] {field}: 未提取到内容")
            all_pass = False
            continue
        match = (value == original_text)
        val_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        status = "PASS ✓" if match else "FAIL ✗"
        print(f"[{status}] 字段 {field}")
        print(f"         SHA-256：{val_hash}")
        if not match:
            all_pass = False
            print(f"         提取内容：{repr(value)}")

    print("\n" + "="*60)
    if all_pass:
        print("  ✅ 所有字段验证通过：压缩解压后元数据完整保留！")
    else:
        print("  ❌ 部分字段验证失败，请检查上方输出。")
    print("="*60 + "\n")
    return all_pass


# ─────────────────────────────────────────────────────────────────────────────
# 主流程（嵌入 + 验证）
# ─────────────────────────────────────────────────────────────────────────────
def main_embed_and_verify():
    print("\n【MP3 元数据隐写演示】\n")

    # 读取原始文本
    with open(TXT_PATH, "r", encoding="utf-8") as f:
        original_text = f.read()
    print(f"[0] 读取原始文本：{TXT_PATH}  ({len(original_text)} 字符)")

    # 生成 MP3
    create_silent_mp3(MP3_PATH)

    # 嵌入元数据
    embed_text_into_mp3(MP3_PATH, original_text)

    # 压缩 → 解压
    unzipped_mp3 = compress_and_decompress(MP3_PATH, ZIP_PATH, UNZIP_DIR)

    # 从解压后的 MP3 提取
    print("\n[4] 从解压后的 MP3 提取元数据...")
    extracted = extract_text_from_mp3(unzipped_mp3)

    # 验证
    verify(original_text, extracted)


# ─────────────────────────────────────────────────────────────────────────────
# 仅提取模式（供后续单独使用）
# ─────────────────────────────────────────────────────────────────────────────
def main_extract_only(mp3_path: str = MP3_PATH):
    """直接从指定 MP3 文件提取隐藏文本并打印。"""
    print(f"\n【从 MP3 提取隐藏元数据】\n目标文件：{mp3_path}\n")
    extracted = extract_text_from_mp3(mp3_path)
    for field, value in extracted.items():
        print(f"── {field} ──")
        print(value if value else "(空)")
        print()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) == 2:
        # 用法：python3 extract_metadata.py <mp3文件路径>
        main_extract_only(sys.argv[1])
    else:
        # 无参数：执行完整嵌入+验证流程
        main_embed_and_verify()
