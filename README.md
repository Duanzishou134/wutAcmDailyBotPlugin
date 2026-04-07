# wut_acm_plugin

用于 AstrBot 的 WUT ACM 每日一题插件，提供 Codeforces 账号绑定、每日题目、积分榜、CF 工具与图片功能。

## 已实现功能
- 账号绑定：/register 通过提交 CE 验证并与 QQ 绑定。
- 每日一题：随机题目获取、提交校验与手动换题。
- 积分榜：按积分排序展示前十。
- 用户信息：/info 本地渲染图片卡片，失败回退文本；/info -t 直接文本。
- CF 工具：随机题目（按难度/标签过滤）、近期比赛（CF/AtCoder/Nowcoder）、用户资料卡。
- 图片管理：按前缀取图、图片列表、图片添加（哈希去重）与图片删除。

## 指令一览
### 账号绑定
- /register <your_codeforces_name>
- /register finish

### 每日一题
- /daily problem
- /daily finish
- /daily change
- /rank

### 用户信息
- /info
- /info -t

### CF 功能
- /cf
- /cf help
- /cf help tags
- /cf random
- /cf random <rating>
- /cf random <low-high>
- /cf random tag=<tag>
- /cf random rating=<low-high> tag=<tag1,tag2>
- /cf contests [count]
- /cf info <handle>

### 图片管理
- /pic <pic_name>
- /pic list [pic_name]
- /add_pic <pic_name> <pic> [-n | -no-suffix]
- /del <pic_name>

## 使用说明
- /register 会要求在 2 分钟内提交 1A 的 CE 代码完成验证。
- /daily finish 会校验当天题目是否通过（verdict=OK）。
- /rank 显示积分榜前十。
- /info 默认返回图片卡片，失败回退文本；/info -t 直接文本。
- /cf random 支持难度区间与标签组合，标签需全部包含。
- /cf contests 默认 8 条，最大 20 条。
- /pic 支持前缀匹配，多图冲突时会提示可选名称。
- /add_pic 支持直接发送图片或回复图片消息，保存时会计算图片哈希（SHA-256 后对 1e9+7 取模）并作为后缀。
- /add_pic 在添加前会按哈希检测重复图片，若已存在则返回已有图片名称，不会重复上传。
- pic 库首次加载会执行一次重构迁移：旧随机后缀或无后缀图片会统一改为 哈希后缀，同时清理重复内容。
- /del 支持按前缀删除；若前缀命中多个图片，会返回候选图片名供二次指定。
- 图片大小限制为 5MB。

## 目录说明
- docs：模块细节说明，见 docs/modules.md。
- service：业务逻辑（用户、每日一题、图片）。
- utils：Codeforces API 辅助。
- pojo：数据模型。

## 正在规划的功能
- 暂无
