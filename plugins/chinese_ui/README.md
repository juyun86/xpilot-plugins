# Chinese UI

简体中文界面语言插件。安装、升级、启停或卸载后完整重启软件或设备生效，关闭后恢复原语言；
不修改系统 LanguageSetting，不增加进程，不发送 CAN，也不改变驾驶行为。

宿主需要提供 ui_language hook 和 role:ui.language 的独占裁决。
旧宿主会通过 requires 检查拒绝安装，不会出现开关存在却无效果的情况。

词条在 translations.json，字体与许可证随插件离线打包。模型名、参数键、插件 ID、
网络名和用户输入不作为翻译源；动态技术错误可能保留英文供诊断。

字体来自 https://github.com/notofonts/noto-cjk/tree/main/Sans ，遵循随包 OFL.txt。
旧版 sunnypilot 简体中文词条作为基础；新增 xpilot 菜单及插件词条保存在同一字典。
更新词条时必须校验格式占位符，并对实际设备的中文字体、换行和开关回退进行检查。

接口说明见仓库 docs/ui-language-api.md；完整协议见系统仓库
https://github.com/juyun86/xpilot/blob/xpilot/docs/design/xpilot-ui-language-api.md 。
语言包提供 code、font、translations，不热更新，不自动翻译未标记的界面原文。
校验失败会记录故障并沿用基础语言，插件开关不会被自动关闭。
功能开关和软件页的动态文字必须先翻译模板再填值；原始更新状态、模式索引与颜色键保持不变。

1.1.0 使用 ExtChineseUI，并要求宿主 params_abi=1。新键尚无值时只读兼容旧 XpilotChineseUI；
显式的新开关值优先，旧文件保留供回退使用。增加文本/秘密输入页和动态设置标题的词条。
