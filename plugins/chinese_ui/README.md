# Chinese UI

简体中文界面语言插件。安装并启用后重启界面生效，关闭或卸载后重启恢复原语言；
不修改系统 LanguageSetting，不增加进程，不发送 CAN，也不改变驾驶行为。

宿主需要提供 ui_language hook 和 role:ui.language 的独占裁决。
旧宿主会通过 requires 检查拒绝安装，不会出现开关存在却无效果的情况。

词条在 translations.json，字体与许可证随插件离线打包。模型名、参数键、插件 ID、
网络名和用户输入不作为翻译源；动态技术错误可能保留英文供诊断。

字体来自 https://github.com/notofonts/noto-cjk/tree/main/Sans ，遵循随包 OFL.txt。
旧版 sunnypilot 简体中文词条作为基础；新增 xpilot 菜单及插件词条保存在同一字典。
更新词条时必须校验格式占位符，并对实际设备的中文字体、换行和开关回退进行检查。
