#!/usr/bin/env python3
"""Build the native Apple Shortcut using only the Python standard library."""

import plistlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


def identifier(name):
    return str(uuid5(NAMESPACE_URL, f"footprint-shortcuts/{name}")).upper()


def text(*parts):
    """Encode text and magic variables using Shortcuts' UTF-16 ranges."""
    value = ""
    attachments = {}
    for part in parts:
        if isinstance(part, str):
            value += part
        else:
            offset = len(value.encode("utf-16-le")) // 2
            attachments[f"{{{offset}, 1}}"] = part["Value"]
            value += "\ufffc"
    result = {"string": value}
    if attachments:
        result["attachmentsByRange"] = attachments
    return {"WFSerializationType": "WFTextTokenString", "Value": result}


def dictionary(*items):
    """Keep numeric JSON fields numeric instead of formatting localized text."""
    return {
        "WFSerializationType": "WFDictionaryFieldValue",
        "Value": {
            "WFDictionaryFieldValueItems": [
                {"WFKey": text(key), "WFItemType": kind, "WFValue": value}
                for key, value, kind in items
            ]
        },
    }


def build_shortcut():
    actions = []

    def add(action, name=None, **parameters):
        if name:
            parameters.update(UUID=identifier(name), CustomOutputName=name)
        actions.append(
            {
                "WFWorkflowActionIdentifier": f"is.workflow.actions.{action}",
                "WFWorkflowActionParameters": parameters,
            }
        )
        if name:
            return {
                "WFSerializationType": "WFTextTokenAttachment",
                "Value": {
                    "Type": "ActionOutput",
                    "OutputUUID": identifier(name),
                    "OutputName": name,
                },
            }

    add(
        "comment",
        WFCommentActionText=(
            "添加快捷指令后, 先填写下面两个文本操作, 再运行.\n\n"
            "第一个: 手机可访问的完整上报地址, 必须包含 /api/location.\n"
            "例如: https://footprint.example.com/api/location\n\n"
            "第二个: config.toml 中的 server.ingest_token, 不要添加 Bearer 前缀."
        ),
    )
    endpoint = add("gettext", "服务地址", WFTextActionText="")
    token = add("gettext", "访问令牌", WFTextActionText="")

    for name, value in [("服务地址", endpoint), ("访问令牌", token)]:
        group = identifier(f"configure-{name}")
        add(
            "conditional",
            GroupingIdentifier=group,
            WFControlFlowMode=0,
            WFCondition=101,
            WFInput={"Type": "Variable", "Variable": value},
        )
        add(
            "alert",
            WFAlertActionTitle="Footprint 配置未完成",
            WFAlertActionMessage=f"请在快捷指令顶部的文本操作中填写{name}.",
            WFAlertActionCancelButtonShown=False,
        )
        add("exit")
        add("conditional", GroupingIdentifier=group, WFControlFlowMode=2)

    position = add("getcurrentlocation", "当前位置")
    observed_at = add("date", "定位时间", WFDateActionMode="Current Date")
    longitude = add(
        "properties.locations",
        "经度",
        WFInput=position,
        WFContentItemPropertyName="Longitude",
    )
    latitude = add(
        "properties.locations",
        "纬度",
        WFInput=position,
        WFContentItemPropertyName="Latitude",
    )
    altitude = add(
        "properties.locations",
        "海拔",
        WFInput=position,
        WFContentItemPropertyName="Altitude",
    )
    city = add(
        "properties.locations",
        "城市",
        WFInput=position,
        WFContentItemPropertyName="City",
    )
    # Use an explicit UTC epoch so the device's time zone cannot shift the timestamp.
    epoch = add(
        "date",
        "Unix 时间起点",
        WFDateActionMode="Specified Date",
        WFDateActionDate="1970-01-01T00:00:00Z",
    )
    seconds = add(
        "gettimebetweendates",
        "Unix 秒数",
        WFTimeUntilFromDate=text(epoch),
        WFInput=text(observed_at),
        WFTimeUntilUnit="Seconds",
    )
    milliseconds = add(
        "math",
        "Unix 毫秒数",
        WFInput=seconds,
        WFMathOperation="\u00d7",
        WFMathOperand="1000",
    )
    timestamp = add(
        "round",
        "毫秒时间戳",
        WFInput=milliseconds,
        WFRoundTo="Ones Place",
        WFRoundMode="Always Round Down",
    )
    utc_offset = add(
        "format.date",
        "UTC 偏移",
        WFDate=text(observed_at),
        WFDateFormatStyle="Custom",
        WFDateFormat="xx",
    )
    # Convert signed HHMM to hours, applying the sign to the minutes as well.
    timezone_expression = add(
        "text.replace",
        "时区换算公式",
        WFInput=text(utc_offset),
        WFReplaceTextFind=r"^([+-])(\d{2})(\d{2})$",
        WFReplaceTextReplace="0 $1 $2 $1 $3 / 60",
        WFReplaceTextRegularExpression=True,
    )
    timezone = add(
        "calculateexpression",
        "时区小时偏移",
        Input=text(timezone_expression),
    )
    device = add("getdevicedetails", "设备名称", WFDeviceDetail="Device Name")
    response = add(
        "downloadurl",
        "服务端响应",
        WFURL=text(endpoint),
        WFHTTPMethod="PUT",
        WFHTTPBodyType="JSON",
        WFHTTPHeaders=dictionary(("Authorization", text("Bearer ", token), 0)),
        WFJSONValues=dictionary(
            ("longitude", text(longitude), 3),
            ("latitude", text(latitude), 3),
            ("altitude", text(altitude), 3),
            ("city", text(city), 0),
            ("timestamp", text(timestamp), 3),
            ("timezone", text(timezone), 3),
            ("device", text(device), 0),
        ),
    )
    record_id = add(
        "getvalueforkey",
        "记录 ID",
        WFInput=response,
        WFGetDictionaryValueType="Value",
        WFDictionaryKey="location.id",
    )

    group = identifier("submission-result")
    add(
        "conditional",
        GroupingIdentifier=group,
        WFControlFlowMode=0,
        WFCondition=100,
        WFInput={"Type": "Variable", "Variable": record_id},
    )
    add(
        "notification",
        WFNotificationActionTitle="Footprint",
        WFNotificationActionBody=text("当前位置已提交. 记录 ID: ", record_id),
        WFNotificationActionSound=False,
    )
    add("conditional", GroupingIdentifier=group, WFControlFlowMode=1)
    add(
        "alert",
        WFAlertActionTitle="Footprint 提交未成功",
        WFAlertActionMessage=text("服务端响应: ", response),
        WFAlertActionCancelButtonShown=False,
    )
    add("conditional", GroupingIdentifier=group, WFControlFlowMode=2)

    return {
        "WFWorkflowClientVersion": "4033.0.4.3",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 4271458815,
            "WFWorkflowIconGlyphNumber": 59738,
        },
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowTypes": [],
        "WFWorkflowActions": actions,
    }


if __name__ == "__main__":
    path = Path(__file__).parent / "upload-location.unsigned.shortcut"
    path.write_bytes(plistlib.dumps(build_shortcut(), sort_keys=False))
    print(f"已生成: {path}")
