# 东方归言录（日服）简体中文汉化

针对 **日服** `jp.goodsmile.touhoulostword_android` 的简体中文汉化工程。通过替换字体、改写主表（master 数据表）、改写剧情 bundle 实现中文化，**不修改 APK**。

> 本项目仅供学习与个人使用。游戏素材与文本版权归原作者及发行方所有，请勿用于商业用途。

---

## 当前进度

| 模块 | 状态 | 说明 |
|---|---|---|
| **主线剧情** | ✅ 100% | 3 个包、5,287 条台词全部简体中文 |
| **剧情选项（二选一）** | ✅ 100% | 454 条 `SelectOrder` 选项全部简体 |
| **玩家应答（按钮式）** | ⬜ **大部分未译** | 361 条 `ButtonOrder.m_strbtn`，约 351 条仍是日文 |
| **角色名字** | ⬜ 部分未译 | 约 300 条 `*_name` 字段仍为日文假名 |
| **主表 86 张** | ✅ 已汉化 | 484,032 字段，其中 102,913 处繁体已转简体 |
| **字体** | ✅ 已替换 | 方正雅宋（简繁全覆盖），解决原日文字体缺简体字形问题 |
| **活动/特别篇剧情** | ⬜ 未翻译 | 5 个包保留原文 |
| **主表日文残留** | ⬜ 未翻译 | 90,633 处（去重 42,203 条），集中在战斗/图鉴类表 |

### 尚未翻译：剧情里的「玩家应答」

剧情中除了台词正文，还有一类**玩家点击回复的按钮文字**，它不在台词字段里，因此本轮未覆盖：

| 脚本类 | 字段 | 总数 | 仍为日文 |
|---|---|---|---|
| `ButtonOrder` | `m_strbtn` | 361 | **约 351** |

样本（日文原文）：

```
ありがとうございます！        → 非常感谢！
はい！                        → 是！
あっ、えっと……！              → 啊，那个……！
面倒をかけてごめんなさい、霊夢さん。
```

此外**角色名字**还有约 300 处未处理（`MessageOrder.m_name`、`LoadUnitOrder.m_name`、`RenameOrder.m_name`），其中一部分是假名（`アリス` → 爱丽丝），另一部分是日文汉字写法（`霊夢` → 灵梦）。

这两项都已列入 `docs/进度与待办.md` 的待办，处理方式与台词一致，只是字段名不同。

### 已知问题（与本项目无关）
**图鉴打开黑屏**：已通过逐层还原（字体 → 主表 → 剧情包 → UI 包全部还原成官方原版）验证，**完全还原后依然黑屏**，更换加速器/VPN 也无效。结论是游戏本体或服务器侧问题，与汉化无关。

---

## 仓库结构

```
scripts/          全部 Python 脚本（扁平放置，脚本间按模块名互相 import）
data/
  table_names.json    表名 → 32 位哈希 映射（212 张表）
  trans_all.json      主表译文全集（86 表 / 484,032 字段 / 30 MB）
  choice_todo.json    剧情选项原文提取结果
bundles/story/    6 个已译好的剧情包（可直接推送）
docs/             技术笔记、进度待办、踩坑记录
AGENTS.md         ★ 给 AI 助手（DSH / Claude 等）的交接说明，接手工作请先读这个
```

---

## 快速上手

### 前置条件

- Windows（脚本用 PowerShell 调用 `adb`）
- Python 3.10+，依赖：`msgpack`、`UnityPy`、`fontTools`、`opencc`
- 一台已 root 的 Android 设备，开启 USB 调试，装好日服客户端并**至少进入过一次游戏**（这样本地才有资源缓存）
- `adb.exe` 放在 `adtools/platform-tools/`

```bash
pip install msgpack UnityPy fonttools opencc
```

### 一分钟验证环境

```bash
# 设备是否在线
adtools/platform-tools/adb.exe devices

# 是否拿到 root（改主表必须有 root）
adtools/platform-tools/adb.exe shell "su -c id"     # 期望 uid=0(root)
```

### 推送现成成果

```bash
# 1) 剧情包（6 个，已译好，直接用）
python lw_bundle_push.py "bundles\story"

# 2) 主表（需先按 docs 说明从日服导出 dumped/，再用 trans_all.json 构建）
python lw_patch.py build data\trans_all.json
python lw_reapply.py tables

# 3) 校验
python lw_reapply.py check
```

> 仓库**不包含**字体二进制文件与 86 张主表成品（`.bin`），因为它们可由脚本从你自己的游戏客户端提取/构建，且字体涉及方正雅宋版权。生成方法见 `docs/技术笔记.md`。

---

## 原理简述

### 1. 字体
日服原字体缺简体字形，直接写简体会显示方块。方案：把国服客户端使用的方正雅宋 TrueType 数据塞进日服的 2 个字体 bundle 的 `Font.m_FontData` 字段。

### 2. 主表（master 表）
游戏的数据表是 **AES-128-CBC/PKCS7 加密的 msgpack**，文件名 = `md5(snake_case(表名) + "_master")`。改法：解密 → 改指定字段 → 重新加密 → 覆盖设备上的同名文件。

### 3. 剧情
剧情台词在 Unity bundle 里的 `MonoBehaviour`，脚本类为 `TalkOrder`（旁白/台词）与 `MessageOrder`，文本字段 `m_text`；玩家选项在 `SelectOrder` 的 `m_strfst` / `m_strsnd` / `m_str3rd`。

脚本内有控制码，必须原样保留：
- `\x1bh` → 玩家名占位符（译文里写作 `{P}`）
- `\x1b` + `mNN`/`fNN` → 表情/颜色切换（译文里写作 `{E}`）

写回后**必须校验 ESC 数量与换行数与原句一致**，否则游戏会出现文字溢出、错行甚至选项错位。

---

## 为什么需要读 AGENTS.md

本工程踩过的坑很多，且多数属于「看起来没问题、实际会让游戏界面坏掉」的类型。例如：

- 剧情译文按「原始行号」绑定会因跳过纯符号行而累积漂移 → 必须按「只数待译行的序号」绑定
- 对 UI bundle 做全字段繁转简会破坏 GameObject 名称查找 → 签到界面物品列表空白、关闭按钮失效
- `{0}` 占位符被翻译破坏会导致 `string.Format` 抛异常

这些细节都写在 `AGENTS.md` 与 `docs/踩坑记录.md` 里。**接手前请务必阅读**，可以省掉大量返工。

---

## 致谢

- 剧情译文为人工翻译（3 个主线包 + 454 条选项）
- 主表部分译文的原始来源：国服客户端数据
- 工具链基于 [UnityPy](https://github.com/K0lb3/UnityPy)、[fontTools](https://github.com/fonttools/fonttools)、[OpenCC](https://github.com/BYVoid/OpenCC)
