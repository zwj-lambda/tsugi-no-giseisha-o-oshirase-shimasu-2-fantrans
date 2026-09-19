# 参与指南

## 准备

- 编辑工具：文本编辑器或 Excel 均可。CSV 为 UTF-8（带 BOM）编码，请勿使用会改变编码或换行风格的工具保存；
- 翻译前先读 `glossary/style-notes.md`（风格指南）并查阅 `glossary/glossary.json`（已冻结术语表）——人名与游戏术语已有定译，请勿另起译名。

## 文本翻译（blocks/ elf/ ui/ prf/）

1. 挑选文件：`blocks/` 下按 `scenario/`（主线）、`keywords/`（关键词话题）、`profile/`（角色档案）、`system/`（系统消息）分类；`elf/`、`ui/`、`prf/` 为外围系统文本；
2. 只修改 `trans` 列（需要备注时加 `note`），**不要改动** `seq` / `anchor` / `orig` 等其他列；
3. `status` 列保持原样即可，维护者复核后统一定稿；可在 `note` 里写上你的 ID 与说明；
4. 遵守 README 中的四条硬约束（CP932 可编码、等长槽位、控制标记保留、command 行不译）；
5. 提交前自检：`python tools/check_csv.py <你修改的文件>`；
6. 发起 PR：标题建议 `[文本] 块文件名`，一个文件一个 PR 最便于复核。

blocks/ 各列含义：

| 列 | 含义 |
|---|---|
| seq | 块内序号（与游戏内行对应，勿改） |
| anchor | 数据区字节偏移（回写锚点，勿改） |
| kind | dialogue / system / binary |
| role | narrative 对白（翻）/ label 标签（照翻）/ command 引擎指令（不翻） |
| orig | 原文（勿改） |
| orig_bytes | 原文 CP932 字节数（译文槽宽参考） |
| trans | 译文（你要填的列） |
| status | 翻译状态（保持原样） |
| note | 备注 |

## 图片文字（images/rule/）

1. 打开 `images/rule/RULE翻译表.csv`，每行对应游戏内「规则说明」页的一处文字；
2. 在「你的译文」列填写你的译法；「现行译文」列是维护者当前采用的版本，供对照；
3. 类型为「同形标注」的行与中文同形、按原样保留像素，除非确有必要请勿改动；
4. 对应效果可参照 `images/preview/` 下同名效果图（按页名对应）。

## 校对

全文校对的六维标准与工作方法见 `review/p7-checklist.md`，欢迎按块认领，在 PR 中说明所校对的块与修改理由。

## 回收与发布

维护者定期把已合并的译文回注游戏文件、重新生成镜像并发布补丁。本仓库只承载翻译文稿，不包含游戏文件。
