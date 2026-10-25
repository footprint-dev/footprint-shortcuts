# Footprint Shortcuts

通过苹果快捷指令向 `footprint-serverful` 上报当前位置.

## 安装配置

1. 从 GitHub Releases 下载 `上传当前位置.shortcut`, 保存到 iPhone 的"文件"中, 点击添加.
2. 打开快捷指令编辑页面, 在顶部第一个"文本"操作中填写完整接口地址, 例如 `https://footprint.example.com/api/location`, 必须包含 `/api/location`.
3. 在第二个"文本"操作中填写后端 `config.toml` 的 `server.ingest_token`, 不加 `Bearer ` 前缀, 然后保存.
4. 手动运行一次, 允许访问位置和服务器, 并开启"精确位置".

配置只需填写一次. 成功后会显示通知和记录 ID. 可添加到主屏幕, 或通过个人自动化中的"运行快捷指令"调用.

## 上报内容

使用 `PUT /api/location` 和 `Authorization: Bearer <token>`, 以 JSON 提交 `longitude`, `latitude`, `city`, `datetime` 和 `device`.

城市和坐标来自同一次定位, 系统未提供城市时为空字符串. 时间使用带时区的 ISO 8601 格式. 每次上报新增记录, 请求超时后应先检查是否已入库再重试.

## 本地生成

需要 Python 3, 签名时需联网访问 [Shortcuty](https://github.com/Shortcuty/Signing-Server-API-Documentation).

```bash
python3 build_shortcut.py
python3 sign_shortcut.py
```

生成的 `上传当前位置.unsigned.shortcut` 用于查看内容, `上传当前位置.shortcut` 用于安装. 修改源码后需重新生成并签名.

## Release 上传

推送 `v*` tag 会触发[工作流](.github/workflows/release.yml), 生成并签名快捷指令, 保存 Actions artifact, 再上传到同名 tag 对应的已有 Release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Release 由你创建和发布, 可以先保留草稿. 如果上传时 Release 尚不存在, 创建后重跑上传任务即可. 重跑会覆盖同名附件.

支持手动运行, 只有 tag 运行会向 Release 上传附件.
