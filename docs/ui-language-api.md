# 界面语言插件接入

完整接口以系统仓库的
[UI 语言包插件 API](https://github.com/juyun86/xpilot/blob/xpilot/docs/design/xpilot-ui-language-api.md)
为准。接口由宿主提供，语言内容由本仓库插件提供。
开发时先读 [Xpilot 最高开发规范](https://github.com/juyun86/xpilot/blob/xpilot/DEVELOPMENT_RULES.md)。接口文档描述实现，不豁免最高规范；已记录的兼容与命名问题须单独整改。

## 能力声明

插件 API 版本为 1。必须同时声明：

~~~json
{
  "claims": ["role:ui.language"],
  "requires": {"hooks": ["ui_language"]}
}
~~~

语言角色独占，按宿主 priority 和插件 ID 裁决。不要通过导入时修改全局函数、
后台改写宿主文件、写 LanguageSetting 或替换控制进程实现汉化。

## 返回值

Plugin 子类的类方法 ui_language() 返回字典：

| 字段 | 内容 |
| --- | --- |
| code | zh-CHS / zh-CHT / ja / ko / th |
| font | 插件内 .otf / .ttf 字体的绝对路径 |
| translations | 英文原文到非空译文的字典，最多 10,000 项 |

示例实现见 [chinese_ui/plugin.py](../plugins/chinese_ui/plugin.py)，
清单见 [plugin.json](../plugins/chinese_ui/plugin.json)。
语言文件、字体和许可证随插件归档；不需要额外常驻进程。

## 使用与更新

- 停车安装、启用后完整重启软件或设备；更新、卸载后也完整重启软件。
- 普通开关值使用自有 ParamsView 键，默认关闭，不修改持久 LanguageSetting。
- 原文须先经过 tr，再填入动态值，再测量和绘制；未标记的文字不会因装插件自动翻译。
- 原文和译文的花括号字段、格式、转换标记及重复次数必须相同。
- 分支名、参数键、模型名、颜色保存值等不随显示翻译改变。
- 字体文件头检查不能证明无缺字；另做字形和真实页面检查。
- 校验失败时宿主记录故障并保留基础语言，不会自动关闭开关。

## 发布前检查

1. 与匹配宿主核对 requires、独占裁决、安装校验。
2. 检查关闭→启用→关闭回退、原 LanguageSetting 不变。
3. 检查字体覆盖、长文字、动态状态及选项动作；特别核对软件更新与功能开关页面。
4. 运行宿主 localization_check、实际 UI import 和页面检查。
5. 运行本仓库 tools/build_index.py，提交源码、dist 和 index.json。
6. 用 Linux 构建器核对归档可重现；压缩包须低于商店 20 MiB 上限。

chinese_ui/README.md 是包内文件，修改时也要重建归档。
只修改本 docs/ 下的接口说明或根 README，不会改变既有插件归档。
