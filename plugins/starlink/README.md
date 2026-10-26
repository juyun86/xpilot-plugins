# Starlink

将原 dev-sp 分支的 mihomo/Clash 上网功能迁移为插件。Starlink 是插件名，不是卫星网络服务。
不增加车辆控制或 CAN 发送接口；后台只负责设备的 IPv4 VPN 上网。

## 安装与操作

适用 AGNOS、Linux ARM64、CPython 3.12。1.1.0 要求宿主支持 processes、ui_glyphs 和 network_vpn。
安装启用后完整重启软件或设备，在大屏 Starlink 磁贴打开控制页。
未显示时可长按主页进入磁贴编辑，添加 Starlink。

- 默认自动连接；可在插件设置里关闭“自动连接”。
- 支持订阅链接、Clash YAML、SS/VMess/VLESS/Trojan 节点链接。
- 可在设备输入，也可让手机加入同一私有 Wi-Fi，扫描临时二维码导入。
- 配对页面只绑定设备当前私有 wlan0 地址，十分钟有效，成功保存一次后关闭。
  页面使用局域网 HTTP，链接包含临时令牌，不应转发；不提供公网管理入口。
- 节点选择保留原始节点身份。连接延迟测试最多测试 128 个节点，延迟不等于下载带宽。
- 测试 GitHub 使用实际 IPv4 TUN 路径，不把本地 API 启动成功当作互联网连接成功。

导入、启停、切换节点等操作要求停车并退出辅助驾驶；已连接时可保持上网。
内核或 TUN 故障会清理并在停车后重连，不保证远端节点或运营商链路可用。
失去守护进程或内核时，独立看守进程清理本插件路由，恢复普通网络；这不是断网保护开关。

## 资源与隐私

沿用 /data/mihomo：mihomo、config.yaml、secret、runtime/、providers/。
首次运行只在设备内备份 config.before-starlink.yaml；不将配置、订阅、节点凭据或令牌写入插件包。
原内核存在时保留，不自动覆盖。新安装缺内核时从随包官方压缩资源解压并验证原始 SHA256。
内核来源、版本与哈希见 core.json；上游许可证见 MIHOMO-LICENSE.txt。

公共 IPv4 经专用 c3mh0 / 表17890路由；本机、RFC1918私网、链路本地和组播保持直连。
不改系统默认路由或 DNS 配置文件；DNS转发和热点规则只使用 C3MH_* 链。
IPv6 没有被本插件全局接管，不能据此宣称全协议流量都经过 VPN。
内核以专用 UID 61400 运行，避免代理自身再次进入 TUN。
若相同 UID、端口17890/17891/17893/17894、接口或路由表被其他服务使用，应先解决冲突。

只复用系统已有 Python/YAML 和宿主二维码组件。后端使用系统 Python 的 YAML 包，
不会为此修改 openpilot 虚拟环境。系统没有 YAML、TUN 或 sudo 权限时显示错误，不应静默安装软件。
节点汉字依赖已选择的语言包字体；ui_glyphs 在 UI 启动时仅取节点显示名补齐字形。
新增订阅带来新文字时，重启软件加载字形。不支持的装饰性非BMP表情可被显示层省略，
但选择节点时始终传递完整原名。

## 生命周期

声明 process:starlinkd、role:network.vpn、ui.glyphs。
ExtStarlinkEnabled 是总开关，默认关闭；ExtStarlinkConnect 是连接意图，默认开启。
Starlink 自有进程在退出后按退避策略重启，不改动宿主其他进程的重启政策。

SIGINT/TERM、停用和卸载会执行清理。工作代码保留只读文件描述符，
保证商店移走插件目录后仍能停止内核并清理路由；无 shell 或任意命令执行接口。
特权操作已移到宿主固定 API，插件不再携带提权脚本；接口及资源归属见
https://github.com/juyun86/xpilot/blob/xpilot/docs/design/xpilot-network-api.md 。
启动、建路由及排队后的操作再次检查停车；清理只处理 root 所记录的自身资源。
磁贴读取有效期 6 秒的 network.vpn 消息；后台失联后下一次刷新显示停止。
私有配置不进入命令行；输入经 stdin，错误不回显原始内核校验输出。

## 维护与验证

源自旧分支 d9522d2098 的 mihomo_manager、mihomo_gateway 和配对流程，已改为插件路径与受管生命周期。
先运行 tests/contract_e2e.py 和 tests/test_backend.py 检查合成边界，再在停车设备运行 tests/parked_e2e.py。
真实 E2E 会短暂重启本插件内核、移除自己的PID标记、损坏自己的TUN并恢复，以验证故障清理。
不得伪造停车/点火状态，也不要输出真实节点、订阅或配对令牌。
发布前运行仓库构建器和宿主商店检查，核对归档小于20 MiB、来源哈希和实装包可复现。

build_native.py 从 core.json 中固定的 Mihomo 源码提交构建 ARM64 ELF，使用 Go 1.26、
with_gvisor、CGO_ENABLED=0、trimpath 和固定 SOURCE_DATE_EPOCH。示例：
python build_native.py --source /path/to/mihomo --go /path/to/go --output /tmp/mihomo
加 --publish 才会替换随包核心和构建元数据；现有设备核心先校验兼容性，不自动覆盖。
该源码重建使用固定时间和随源码 CA，不能把它称为与上游动态时间/CA 的发布资产逐字节相同。
