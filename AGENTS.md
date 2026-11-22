# AGENTS.md — 交接说明（给 AI 助手 / DSH）

> 你如果是接手这个项目的 AI 助手，请先完整读完本文件再动手。
> 本工程有多个「看起来对、实际会把游戏界面搞坏」的陷阱，`docs/踩坑记录.md` 里有真实事故记录。

---

## 0. 一句话现状

日服《东方归言录》简体汉化：**主线剧情台词 100% 完成**（5,287 条台词 + 454 条二选一选项）、主表 86 张已汉化（484,032 字段）、字体已替换为方正雅宋。

**未完成（按优先级）**：
1. **剧情里的「玩家应答」按钮文字** —— `ButtonOrder.m_strbtn`，361 条中约 **351 条仍是日文**（≈97%）。这是玩家点一下回复 NPC 的那句话，**不在台词字段里，极易漏掉**。
2. 主表 90,633 处日文残留（去重 42,203 条）
3. 剧情角色名字约 300 处（`MessageOrder.m_name` / `LoadUnitOrder.m_name` / `RenameOrder.m_name`）
4. 活动剧情 5 个包

接手后最可能的任务是：① 翻译 `ButtonOrder.m_strbtn` ② 翻译主表日文残留 ③ 翻译活动剧情 ④ 有 root 时恢复主表。

---

## 1. 环境与设备事实（不要重新摸索）

| 项 | 值 |
|---|---|
| 游戏包名 | `jp.goodsmile.touhoulostword_android`（日服，**不要动 global 国际服包**） |
| adb 路径 | `adtools/platform-tools/adb.exe` |
| 主表目录 | `/data/data/jp.goodsmile.touhoulostword_android/files/cache/`（**必须 root**） |
| Bundle 缓存 | `/sdcard/Android/data/jp.goodsmile.touhoulostword_android/files/UnityCache/Shared/<A>/<B>/` |
| 设备属主 | `u0_a469:u0_a469`，shell 用户在组 `ext_data_rw`(1078) 内 |

### adb 守护进程起不来的处理

若报 `cannot open ...adb.log: Permission denied`，说明临时目录不可写，改 TMP 即可：

```powershell
$tmp="$PWD\adtmp"; New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$env:TMP=$tmp; $env:TEMP=$tmp
```

### root 相关（重要）

- 目标设备是小米/澎湃 OS。**澎湃 OS 4 起临时 root 方案不稳定**：有的工具授权后立刻关机，关机后 root 消失。
- 判断当前是否有 root：`adb shell "su -c id"`，期望 `uid=0(root) ... context=u:r.ksu:s0`。
- 无 root 时：
  - `adb root` → 生产版直接拒绝
  - `run-as` → 游戏不是 debuggable
  - `appops set com.android.shell MANAGE_EXTERNAL_STORAGE allow` → 只能列目录，**读/写仍被拒**
  - 结论：**主表读写必须有 root**

---

## 2. 目录与关键文件

```
scripts/
  lw_master.py          ★ 主表加解密核心（SECRET / KEY / IV 都在这里）
  lw_patch.py           ★ 由译文 json 构建 out/<表>.bin（加密后可直接覆盖设备文件）
  lw_reapply.py         ★ 一键重推主表 + 剧情包；`check` 子命令做状态核对
  lw_bundle_push.py     ★ 推 bundle 到 UnityCache 并写 __info（需 root）
  lw_bundle_push_nosu.py  免 root 版（依赖缓存文件属组为 ext_data_rw）
  lw_push_clean.py     免 root 推 UI 包
  lw_invalidate.py     把 bundle 的 __info 改成失效，诱使游戏重下官方原版
  lw_cc.py             OpenCC 封装；LW_MODE=sc|tw|t2s
  lw_autocn.py         国服数据 → 译文（同表同名同字段顺序）
  lw_cnpatch.py        从国服汉化包抽取可搬移译文（带占位符/标签安全闸门）
  lw_merge.py          多源译文合并 → trans_all.json
  lw_run_sc.py         简体全管线重跑
  lw_story_*.py        剧情提取 / 回写 / 对齐 / 选项处理
  lw_ui_*.py           界面文字普查 / 导出 / 回写
data/
  table_names.json     表名 → 哈希（212 张）
  trans_all.json       主表译文全集
  choice_todo.json     剧情选项原文
bundles/story/         6 个已译剧情包（成品，可直接推）
```

### 关键常量（在 lw_master.py 里）

- `SECRET` + 字符串 `"MasterMsgPack"` 派生出 AES KEY/IV
- 文件名 = `md5(snake_case(表名) + "_master")`
- 加解密：AES-128-CBC + PKCS7

---

## 3. 标准操作流程

### 3.1 推剧情包（最常用，风险最低）

```bash
python lw_bundle_push.py "bundles\story"
```

脚本会：`am force-stop` 游戏 → push 到 `/data/local/tmp` → `su -c cp` 到目标目录 → 按规范写 `__info` → md5 校验 → 汇总成功/失败数。

`__info` 规范（写错会导致游戏重下、缓存失效）：

```
-1
<epoch>
1
__data
```

其中 `epoch` 必须等于同级 `__data` 的 mtime（秒），且 `__info` 自身 mtime 也要设成同一个 `epoch`。

### 3.2 推主表

```bash
python lw_patch.py build data\trans_all.json   # 生成 out/*.bin
python lw_reapply.py tables                    # 推送 + 校验
python lw_reapply.py check                     # 状态核对
```

> ⚠️ `lw_reapply.py check` 内部用 `su -c md5sum`。**无 root 时会把所有表误报成「已被覆盖」**（因为 md5 取到空串）。无 root 请改用 `lw_status_noroot.py` 核对 UnityCache 部分，主表无法核对。

### 3.3 推 UI 包（两条路）

**有 root：**

```bash
python lw_ui_apply.py --write          # 生成 ui_out（只改 LocalizeText.jpText）
python lw_ui_text_apply.py --write     # 生成 ui_text_out（只改 Text.m_Text）
python lw_bundle_push.py "lw_work\ui_out"
python lw_bundle_push.py "lw_work\ui_text_out"
```

**无 root（应急通道，见 §5）：**

```bash
python lw_push_clean.py
```

### 3.4 加新剧情译本

1. `python lw_story_prompt.py <A>/<B> <起> <迄>` 按**序号**打印待译行（序号只数含假名的行）
2. 译文写成 Python 模块：`SC = {1: '...', 2: '...'}`，`ORDINAL=True`、`ALLOW_PARTIAL=True`
3. `python lw_story_apply.py lw_story_sc_xxx --write`
4. **必须**校验 ESC 数与换行数，全部为 0 差异才推

---

## 4. 校验规则（每次写回后必做）

剧情/主表写回后，逐条与原文比对：

1. `\x1b`（ESC）数量必须**完全相等**
2. 换行 `\n` 数量必须**完全相等**
3. 玩家名占位符：原文有 `\x1bh`，译文必须有 `{P}`（会被还原成 `\x1bh`）
4. 主表额外项：
   - 若原文可被 `json.loads`，译文也必须可解析且**深度相等**
   - 原文是纯数字串 → 译文必须仍是纯数字
   - 原文无 `{n}` 占位符 → 译文**不得新增**（否则 `string.Format` 抛异常）
   - 富文本标签集合（`<color=...>` 等）应一致

现成脚本：`lw_data_integrity.py`、`lw_semantic_check.py`、`lw_ph_check.py`、`lw_audit2.py`。

---

## 5. 无 root 应急通道（重要发现）

如果设备暂时拿不到 root，但需要修 bundle：

1. **`__info` 是组可写的**（属于 `ext_data_rw`，shell 在该组），而 `__data` 与目录不可写。
2. 把 `__info` 的 epoch 改成与 `__data` mtime **不一致**的值，即让缓存失效：

```bash
# 例：把 epoch 写成 1
printf -- '-1\n1\n1\n__data\n' > <dir>/__info
```

3. 启动游戏，它会**自动重新下载官方原版包**。
4. 重新下载后的文件属组会变成 `u0_a469:ext_data_rw`（组可写），**此时 shell 就能直接覆盖 `__data`**，无需 root。

现成脚本：`lw_invalidate.py`（批量失效）、`lw_check_redownload.py`（看重下进度）、`lw_push_clean.py`（重下后推干净版）。

> 取舍：这会先把那批 bundle 恢复成**官方日文**。适合「汉化把界面搞坏了，先让游戏能用」的场景。

---

## 6. 接下来可以做什么（任务清单）

### A. 剧情玩家应答（`ButtonOrder.m_strbtn`）—— 强烈建议先做

**这是目前最明显的缺口**：主线 3 包共 361 条，约 **351 条仍是日文**。

这是玩家点击后回复 NPC 的那句话，例如：

```
ありがとうございます！  →  非常感谢！
はい！                  →  是！
面倒をかけてごめんなさい、霊夢さん。 → 给您添麻烦了，灵梦小姐。
```

它**不在 `m_text` 里**，所以只翻台词会整片漏掉。处理方式与台词完全相同，只是字段名换成 `m_strbtn`：

1. 在剧情 bundle 里遍历 `MonoBehaviour`，取脚本类为 `ButtonOrder` 的对象
2. 翻译 `m_strbtn` 字段
3. 写回并校验 ESC 数 / 换行数

现成脚本 `lw_story_fields_audit.py` 可复核各字段的未译数量。

同一批还应处理**角色名字**（约 300 处）：

| 脚本类 | 字段 | 说明 |
|---|---|---|
| `MessageOrder` | `m_name` | 说话人名字 |
| `LoadUnitOrder` | `m_name` | 立绘单位名 |
| `RenameOrder` | `m_name` | 名字变更显示 |

注意名字有两种情况都要管：
- 假名写法：`アリス` → 爱丽丝
- 日文汉字写法：`霊夢` → 灵梦、`魔理沙` 不变

### B. 主表日文残留（最大工作量）

现状：90,633 处含假名 → **去重后 42,203 条**。分布：

| 类别 | 表 | 去重条数 |
|---|---|---|
| 战斗 | Bullet / SkillEffect / Skill / Resist | 约 30,500 |
| 收藏 | Voice / Enemy / Bgm / Picture | 约 7,100 |
| 其他 | Shot / Spellcard / Mission / Ability 等 | 约 4,500 |

重要事实：这些字段 **国服客户端本身也没有译文**（75,220 处国服同样是日文，14,930 处是国服没有的新增行），所以**没法靠对齐国服自动生成**，需要真实翻译。

建议流程：`lw_ja_dedup.py` 导出 → 分批人工/AI 翻译 → 合并进 `trans_all.json` → `lw_patch.py build` → 推。

### C. 活动剧情

5 个包未译（保留原文）。用 §3.4 的流程即可，注意活动包量大、需分批。

### D. 图鉴黑屏

已验证与汉化无关（全量还原官方后仍黑屏）。如需继续排查，方向是游戏本体/服务器/账号数据，不是本地文件。

### E. 主表恢复（如果被游戏版本更新冲掉）

游戏在**版本更新/资源下载**时会重写 `files/cache`。届时：

```bash
python lw_reapply.py tables
```

---

## 7. 千万不要做的事

1. **不要对 UI bundle 做「全字段」繁转简。** 只允许改 `LocalizeText.jpText` 和 `Text.m_Text`。曾因全字段 t2s 破坏 GameObject 名称查找，导致签到界面物品列表空白、× 按钮失效。
2. **不要按「原始行号」给剧情挂译文。** 必须按「只数待译行的序号」绑定，否则遇到纯符号行会累积漂移。
3. **不要 t2s 往返繁体。** `s2twp → t2s` 往返约 10% 失真（通过→透過→透过），简体模式应从源头不做转换（`LW_MODE=sc`）。
4. **不要动国际服包**（`jp.goodsmile.touhoulostwordglobal_android`）。
5. **不要在未校验的情况下推算成功。** 每次推送都要看 md5 校验结果与差异计数。
6. **不要假设 `lw_reapply.py check` 在无 root 时可信**（见 §3.2 警告）。
7. **翻译时不要改动 `{P}` / `{E}` / `{n}` 占位符与换行数。**

---

## 8. 详细资料

- `docs/技术笔记.md` — 加密算法、bundle 结构、缓存机制、字体替换原理
- `docs/进度与待办.md` — 逐包进度、条数、待办清单
- `docs/踩坑记录.md` — 真实事故与修复方法（强烈建议阅读）
