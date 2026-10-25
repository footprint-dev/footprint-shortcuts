#!/usr/bin/env python3
"""Sign the generated shortcut using the Shortcuty signing API."""

from pathlib import Path
from urllib.request import Request, urlopen


def sign_shortcut(source, destination):
    request = Request(
        "https://sign.shortcuty.app/api/v1/sign",
        data=source.read_bytes(),
        headers={
            "Content-Type": "application/octet-stream",
        },
    )
    with urlopen(request, timeout=45) as response:
        signed = response.read()
    if not signed.startswith(b"AEA1"):
        raise ValueError("签名服务未返回 AEA1 快捷指令文件.")
    destination.write_bytes(signed)


if __name__ == "__main__":
    root = Path(__file__).parent
    destination = root / "Footprint 提交当前位置.shortcut"
    sign_shortcut(root / "Footprint 提交当前位置.unsigned.shortcut", destination)
    print(f"已签名: {destination}")
