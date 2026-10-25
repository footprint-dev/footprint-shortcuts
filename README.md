# Footprint Shortcuts

向 `footprint-serverful` 提交当前位置的苹果快捷指令. 使用系统自带操作获取位置和设备名称, 调用 `PUT /api/location`, 成功后显示通知.

## 安装

1. 从本仓库 GitHub Releases 的 Assets 下载 `Footprint 提交当前位置.shortcut`, 保存到 iPhone 的"文件"中, 点击文件并添加到"快捷指令".
2. 添加后打开快捷指令的编辑页面, 在顶部说明下面的第一个"文本"操作中填写手机可访问的完整接口地址, 例如 `https://footprint.example.com/api/location`. 地址需包含 `/api/location`; 手机上的 `localhost` 指手机自身.
3. 在第二个"文本"操作中填写后端 `config.toml` 中的 `server.ingest_token`, 不要添加 `Bearer ` 前缀, 然后保存.
4. 手动运行一次, 允许快捷指令访问位置和服务器. 在系统定位权限中开启"精确位置".

安装时不弹出配置问题, 避开 iOS 26 在填写导入参数后无法完成添加的情况. 该原生页面卡住的具体原因尚未确认, 当前采用添加后编辑配置的方式. 地址或 Token 未填写时, 运行会提示补全配置并停止, 不会定位或发送请求.

安装文件使用中文名称, 导入后的快捷指令名称为 `Footprint 提交当前位置`.

以后点击运行即可. 也可以在快捷指令详情中添加到主屏幕, 或在个人自动化中通过"运行快捷指令"调用它.

## 提交内容

| 字段 | 来源 |
| --- | --- |
| `longitude` | 本次定位的经度, JSON 数字 |
| `latitude` | 同一次定位的纬度, JSON 数字 |
| `city` | 同一次定位的城市名称, 系统未提供时为空字符串 |
| `datetime` | 获取位置后的当前时间, 包含时区的 ISO 8601 字符串 |
| `device` | 系统设备名称 |

请求使用 JSON, 鉴权头为 `Authorization: Bearer <token>`. 地址和 Token 保存在快捷指令顶部的两个文本操作中, 每次运行不再询问.

只提交上述五个字段. 城市名称由系统从当前位置取得, 不另行定位. 未提交的 `timezone` 保存为 `null`; `datetime` 中的时区用于解析时间戳, 不会自动填入 `timezone` 字段.

返回内容含 `location.id` 时显示成功通知和记录 ID, 因此服务端已保存位置但 `analysis.state` 为 `deferred` 时也算提交成功. 其他 JSON 响应会显示为提交失败提示; 定位、网络或响应解析错误由快捷指令系统显示.

每次运行只发送一次请求. 后端每次上报都会新增记录, 请求超时后应先检查是否已经入库, 再决定是否重试.

## Release 附件上传

仓库保存 Python 源码、工作流和文档. 两种 `.shortcut` 产物均被 `.gitignore` 忽略, 本地文件仅用于调试, 安装文件通过 Release 分发.

与前端仓库一致, [附件上传工作流](.github/workflows/release.yml) 在推送 `v*` tag 时触发, 也可以通过 `workflow_dispatch` 手动运行:

```bash
git tag v0.1.0
git push origin v0.1.0
```

构建任务运行签名错误处理的回归测试, 生成并签名快捷指令, 将 `Footprint 提交当前位置.shortcut` 保存为 Actions artifact `shortcut-release`. 只有 tag 运行才会进入上传任务, 下载该 artifact 并使用 `gh release upload` 上传到同名 tag 对应的已有 Release.

上传前需要你创建对应 Release, 可以先保持草稿; Release 的发布和发布说明由你管理. 如果上传时 Release 尚不存在, 创建后重新运行失败的上传任务即可. 在分支上手动运行只构建 Actions artifact. 上传任务单独使用 `contents: write` 权限和 GitHub 自动提供的 `GITHUB_TOKEN`; 重新运行会覆盖同名附件.

GitHub 托管的 macOS runner 没有登录 iCloud, 无法直接使用需要该登录状态的 `shortcuts sign`. 因此工作流使用 Shortcuty 远程签名, 不依赖 runner 上的 Apple 账号. 参见 [shortcutkit 的签名环境说明](https://github.com/frontboat/shortcutkit) 和 [Shortcuty API 文档](https://github.com/Shortcuty/Signing-Server-API-Documentation).

签名服务会收到生成的完整模板. 模板不包含真实服务地址和 Token, 这些配置在用户导入后填写. 服务不可用或返回无效文件时工作流会失败, 可在服务恢复后重新运行失败的任务.

签名步骤的 HTTP 403 来自签名服务拒绝请求, 与 GitHub Release 上传权限无关. 脚本会输出状态码、响应类型、前 4096 字节响应正文和 `CF-Ray`, 用于区分服务接口报错与访问防护拦截. 如果服务持续拒绝 GitHub runner 的请求, 需由签名服务维护者排查和放行; 也可在已登录 iCloud 的 Mac 上按下文方式签名. 本地签名成功不能确认 GitHub runner 的请求也已被放行.

## 本地调试

两个脚本只使用 Python 标准库. 在本目录运行与 CI 相同的生成和签名步骤:

```bash
python3 -m unittest discover -s tests
python3 build_shortcut.py
python3 sign_shortcut.py
```

生成的 `Footprint 提交当前位置.unsigned.shortcut` 是可查看的 XML, `Footprint 提交当前位置.shortcut` 是可导入的已签名文件. 本地修改后需重新运行两个步骤, 已有签名文件不会随源码自动更新.

签名成功只表示生成了签名容器, 不代表所有动作参数都能被 iOS 正确解析; 修改生成器后仍需在目标 iOS 版本上实际完成添加、填写顶部配置和运行. 当前签名流程会移除 plist 中的 `WFWorkflowName`, 因此不能依赖该字段将导入标题与文件名分开设置.

在已登录 iCloud 的 Mac 上, 也可以在生成后用苹果工具签名:

```bash
shortcuts sign --mode anyone \
  --input "Footprint 提交当前位置.unsigned.shortcut" \
  --output "Footprint 提交当前位置.shortcut"
```

签名命令见 [Apple 官方文档](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac). 手动导入后运行, 看到记录 ID 再在服务端确认记录, 即可检查实际定位和上报. 分享已配置的快捷指令前需清空 Token.
