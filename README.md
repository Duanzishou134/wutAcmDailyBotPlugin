# wut_acm_plugin

用于 AstrBot 的 WUT ACM 每日一题插件，提供 Codeforces 账号绑定、每日题目、积分榜与图片功能。

## 已实现功能
- 账号绑定：/register 与 /register finish。
- 每日一题：/daily problem、/daily finish、/daily change。
- 积分榜：/rankist（前十）。
- 用户信息：/info。
- 图片管理：/pic、/add_pic。

## 指令一览
- /register <your_codeforces_name>
- /register finish
- /daily problem
- /daily finish
- /daily change
- /rankist
- /info
- /pic <pic_name>
- /pic -list [pic_name]
- /add_pic <pic_name> <pic> [-n | -no-suffix]

## 目录说明
- docs：模块细节说明，见 docs/modules.md。
- service：业务逻辑（用户、每日一题、图片）。
- utils：Codeforces API 辅助。
- pojo：数据模型。

## 正在规划的功能
- /info 输出图片而非文本。
