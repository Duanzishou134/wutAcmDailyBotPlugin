# 模块细节

## main.py
- 入口注册插件并初始化数据库与各类 service。
- 指令层：
  - /register 与 /register finish 账号绑定流程。
  - /daily problem /daily finish /daily change 每日一题流程。
  - /rankist 积分榜（前十）。
  - /pic /add_pic 图片功能。

## service/user_service.py
- 注册起始：写入用户与注册状态，记录 start_time。
- 注册完成：检查 2 分钟有效期，异步校验 CF 编译错误提交。
- 排行榜：按 rating 降序取前十。

## service/daily_problem_service.py
- 每日一题：当天有记录则复用，否则从 CF 题库随机抽题并落库。
- 完成判定：检查用户提交 OK、更新积分并写入 user_problem。
- 变更题目：重新抽题并更新当天记录。

## service/pic_service.py
- 图片目录：确保 pic 目录存在。
- 图片列表：过滤 jpg/png/jpeg/gif。
- 图片匹配：支持 pic_name 与 pic_name-* 的随机返回。
- 图片添加：支持自动后缀或固定名；限制 5MB。

## utils/codeforces_utils.py
- CF API：user.status 与 problemset.problems。
- 校验逻辑：匹配 contestId/index、判定 verdict。
- 随机题：按 rating 与标签过滤。

## database.py
- SQLModel + SQLite。
- 初始化：插件启动时创建表。

## pojo/*.py
- User：CF 账号绑定、积分与注册状态。
- DailyProblem：每日题目与日期。
- UserProblem：用户完成记录。
