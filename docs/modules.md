# 模块细节

## main.py
- 入口注册插件并初始化数据库与各类 service。
- 指令层：
  - /register 与 /register finish 账号绑定流程。
  - /daily problem /daily finish /daily change 每日一题流程。
  - /rankist 积分榜（前十）。
  - /info 用户信息查询（本地渲染图片卡片，失败回退文本），/info -t 输出文本。
  - /pic /add_pic 图片功能。

## service/user_service.py
- 注册起始：写入用户与注册状态，记录 start_time。
- 注册完成：检查 2 分钟有效期，异步校验 CF 编译错误提交。
- 排行榜：按 rating 降序取前十。
- 用户信息：查询本地绑定信息并聚合 CF 用户信息与做题数量。

## service/daily_problem_service.py
- 每日一题：当天有记录则复用，否则从 CF 题库随机抽题并落库。
- 完成判定：检查用户提交 OK、更新积分并写入 user_problem。
- 变更题目：重新抽题并更新当天记录。

## service/pic_service.py
- 图片目录：确保 pic 目录存在。
- 图片列表：/pic -list 仅返回最后一个 '-' 前的名称；支持前缀过滤。
- 图片匹配：前缀匹配；若精确前缀后跟 '-' 则随机返回，否则单个返回，多条提示冲突。
- 图片添加：支持自动后缀或固定名；限制 5MB。

## utils/codeforces_utils.py
- CF API：user.status 与 problemset.problems。
- 用户信息：user.info。
- 做题统计：拉取提交并统计去重的 OK 数量。
- 校验逻辑：匹配 contestId/index、判定 verdict。
- 随机题：按 rating 与标签过滤。

## utils/html_render.py
- 本地 HTML 模板渲染：Jinja2 + Playwright（优先使用本机 Edge/Chrome）。

## database.py
- SQLModel + SQLite。
- 初始化：插件启动时创建表。

## pojo/*.py
- User：CF 账号绑定、积分与注册状态。
- DailyProblem：每日题目与日期。
- UserProblem：用户完成记录。
