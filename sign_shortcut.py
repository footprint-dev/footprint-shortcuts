#!/usr/bin/env python3
"""Sign the generated shortcut using the Shortcuty signing API."""

from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def sign_shortcut(source, destination):
    request = Request(
        "https://sign.shortcuty.app/api/v1/sign",
        data=source.read_bytes(),
        headers={
            "Content-Type": "application/octet-stream",
            "User-Agent": "footprint-shortcuts",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            signed = response.read()
    except HTTPError as error:
        with error:
            detail = error.read(4096).decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"签名服务请求失败: HTTP {error.code}; "
            f"Content-Type: {error.headers.get('Content-Type', '未提供')}; "
            f"CF-Ray: {error.headers.get('CF-Ray', '未提供')}\n"
            f"{detail or '响应正文为空'}"
        ) from error
    if not signed.startswith(b"AEA1"):
        raise ValueError("签名服务未返回 AEA1 快捷指令文件.")
    destination.write_bytes(signed)


if __name__ == "__main__":
    root = Path(__file__).parent
    destination = root / "Footprint 提交当前位置.shortcut"
    try:
        sign_shortcut(root / "Footprint 提交当前位置.unsigned.shortcut", destination)
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from None
    print(f"已签名: {destination}")
