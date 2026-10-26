# xpilot-plugins

Plugin repository for [xpilot](https://github.com/juyun86/xpilot) (Tesla-only sunnypilot fork; upstream: onemiless).
Devices list this repository under Settings → Plugins → Plugin Store, install while parked, and apply on restart.

Development starts with the canonical [Xpilot highest development policy](https://github.com/juyun86/xpilot/blob/xpilot/DEVELOPMENT_RULES.md) and this repository's [AGENTS.md](AGENTS.md). That policy resolves conflicting project documentation. Current implementation gaps are tracked in its section 8; listing a plugin here does not establish compliance.

插件仓库：xpilot 设备在 设置 → Plugins → Plugin Store 里浏览这里的插件，停车时安装，重启后生效。
接口、类别、资源声明和底线规则见 xpilot 仓库根目录的 `XPILOT.md`。

## Layout

```
plugins/<id>/            plugin source: __init__.py, plugin.json (manifest), plugin.py, optional ui.py and modules
dist/<id>-<ver>.tar.gz   reproducible archives, generated
index.json               what devices read: id, version, api, category, url, sha256, generated
tools/build_index.py     builds dist/ and index.json; --check verifies they are current
```

## Submitting a plugin / 提交插件

1. Fork, add `plugins/<id>/`, open a pull request (see `CONTRIBUTING.md`). Read `XPILOT.md` first.
2. `plugin.json`: `id` equals the directory, `api` is the host's API version (1), a category from `XPILOT.md`,
   required `use` (`onroad`, `offroad`, or `both`) for its usage context,
   `claims` for everything the plugin uses, params with types BOOL/INT/FLOAT/STRING/JSON. Downloaded plugins
   must not reuse built-in ids or param keys; prefix new keys with `Ext`. The plugins moved here from the xpilot
   repository keep their original key names so existing device settings stay valid.
   Tiles must match `use`: `onroad` excludes offroad tiles, `offroad` excludes onroad tiles, and
   `show="always"` requires `both`. This declaration does not change hook runtime conditions.
3. Use relative imports inside the plugin (`from .logic import x`): installed plugins load as `xpilot_ext.<id>`.
4. Prefer pure Python. Compiled code must ship as prebuilt binaries with a `platform` and a `build_native.py`
   that reproduces them (see Native plugins). CAN senders declare `rules` (`template_clone.v1`) and
   `requires: {"rule_abi": 1}`; `can.tx` claims must equal the rules' TX address/bus pairs. The host validates
   and compiles these rules for the Panda runtime engine. Legacy `safety` manifests are rejected;
   there is no translation layer.
5. Run `python3 tools/build_index.py` and commit `dist/` and `index.json` with the source.
6. Describe in the PR what the plugin changes on the road, which claims it takes, and how you tested it.

## Review checklist (maintainer) / 审核清单

- `python3 tools/build_index.py --check` passes on the PR head (archives match the reviewed source).
- From an xpilot checkout: `python3 tools/sp_tesla_e2e/store_e2e.py --repo <this checkout>` passes.
- Claims match the code: every CAN address sent, hook used and managed process started is claimed. Params,
  messages, private files and network operations stay within the documented host API contract. Network access
  requires the explicit capability contract in the highest development policy; it is not granted by a category name.
- Control plugins (lateral, longitudinal, lane change, engagement, ...) state their floors and failure behaviour.
- No obfuscated code, no downloaded or generated code at runtime, and no shell or arbitrary-command interfaces.
  Network/system capabilities require the documented host API, permission and lifecycle contract specified in the highest development policy. A process/role claim or fixed command alone does not provide that contract. The previous Starlink-specific subprocess exception is withdrawn. Starlink now uses the host VPN API; validation results and remaining device boundaries are recorded in section 9 of the canonical policy.

Archives are not signed yet: the sha256 in `index.json` only protects against corrupt or swapped downloads.
Trust comes from this reviewed repository, so only merge what you have read.

## Plugins

- [starlink](plugins/starlink/README.md): mihomo VPN internet access with an offline ARM64 core, local configuration,
  phone import and scoped routing cleanup. Requires the host ui_glyphs capability; not a satellite service.

- [UI 语言包 API](docs/ui-language-api.md)：声明、返回格式、生效时机、校验及发布检查。
- [chinese_ui](plugins/chinese_ui/README.md)：简体中文语言插件，字体和词条随包提供。

- `plugins/overspeed_warning`: example. Alerts category, one store-backed setting, an `alert` claim, a relative import.
- `plugins/tn_long`: TN longitudinal (TN-NoDEC) as a `long_planner`, with prebuilt acados solvers. See its README.
- `plugins/tesla_mixed_control`: dzid26 angle-based cooperative steering. Enable while parked and restart;
  SP must own steering and stock Autosteer must not steer concurrently. See its README for timing and host-only validation limits.

Moved from the xpilot repository (keep their original param keys):

- Display, installed by default on first boot: `speed_card`, `lead_card`, `speed_limit_card`, `car_tile`, `map_tile`,
  `clock_tile`, `ip_tile`, `blindspot_edges`.
- `bms`: battery tile. `traffic_light`: traffic light stop/start. `external_compute`: external compute bridge.
- Runtime Panda rules (need host/firmware ABI 1): `auto_speed` (0x3C2), `ambient_light` (0x679), both 1.1.0.
  The old 1.0.x archives are withdrawn. Merge the X-33 host support before this plugin release.

Tests: `cd plugins && python3 -m pytest -q .` with an xpilot checkout on `PYTHONPATH` (see `.github/workflows/ci.yml`).
Run `python3 tools/runtime_rules_check.py --output /tmp/runtime-rules` with that same `PYTHONPATH` to validate
source and archives against the real host, compare AUTO/AMBIENT reference bytes and exercise card setup.
It saves `result.json` with source identities/hashes, table binaries and the CRC-bearing card param.

## Native plugins / 带二进制的插件

Plugins with compiled code ship prebuilt binaries for one platform: `plugin.json` gets
`"platform": {"machine": "aarch64", "python": "cpython-312"}` (written by the plugin's `build_native.py`, run on the
target device). Devices only offer and load a native plugin on a matching platform. Binaries cannot be reviewed like
source: review the build script, and rebuild them yourself on your device before merging.
