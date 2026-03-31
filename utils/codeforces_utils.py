import random

import aiohttp
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, date
from ..config import Config


class CodeforcesUtils:

    async def get_user_submissions(self, codeforces_name: str, count: int = 30) -> Optional[List[Dict]]:
        """获取用户最近的提交记录"""
        url = f"{Config.CF_API_URL}/user.status"
        params = {"handle": codeforces_name, "count": count}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if data["status"] == "OK":
                        return data["result"]
                    return None
            except Exception as e:
                print(f"CF API错误: {e}")
                return None

    async def get_user_info(self, codeforces_name: str) -> Optional[Dict]:
        """获取用户信息"""
        url = f"{Config.CF_API_URL}/user.info"
        params = {"handles": codeforces_name}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if data.get("status") == "OK" and data.get("result"):
                        return data["result"][0]
                    return None
            except Exception as e:
                print(f"CF API错误: {e}")
                return None

    async def get_solved_count(self, codeforces_name: str) -> Optional[int]:
        """获取用户已解决题目数量（去重后的 OK 提交）"""
        url = f"{Config.CF_API_URL}/user.status"
        params = {"handle": codeforces_name, "from": 1, "count": 10000}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if data.get("status") != "OK":
                        return None
                    solved = set()
                    for sub in data.get("result", []):
                        if sub.get("verdict") != "OK":
                            continue
                        problem = sub.get("problem", {})
                        contest_id = sub.get("contestId")
                        index = problem.get("index")
                        if contest_id is None or index is None:
                            continue
                        solved.add((contest_id, index))
                    return len(solved)
            except Exception as e:
                print(f"CF API错误: {e}")
                return None


    async def check_submission(
            self,
            codeforces_name: str,
            contest_id: int,
            problem_index: str,
            verdict: str,
            sub_date: date
    ):
        submissions = await self.get_user_submissions(codeforces_name, count=30)
        if not submissions:
            return False
        for sub in submissions:
            # 检查提交时间
            submission_time = sub.get("creationTimeSeconds", 0)
            submission_date = datetime.fromtimestamp(submission_time).date()
            # 转换为 datetime
            if sub_date and submission_date != sub_date:
                continue

            # 检查题目ID (contestId/problemId)
            problem = sub.get("problem", {})

            if sub.get("contestId") != contest_id or problem.get("index") != problem_index:
                continue

            if sub.get("verdict") == verdict:
                return True
        return False

    async def check_ce_submission(self, codeforces_name: str, start_time: int) -> bool:
        """
        检查用户在指定时间后是否提交了CE代码到1A题
        start_time: Unix时间戳(秒)
        """
        submissions = await self.get_user_submissions(codeforces_name, count=30)
        if not submissions:
            return False

        for sub in submissions:
            # 检查提交时间
            if sub.get("creationTimeSeconds", 0) < start_time:
                continue

            # 检查题目ID (contestId/problemId)
            contest_id = sub.get("contestId")
            problem = sub.get("problem", {})
            problem_index = problem.get("index")

            # 必须是 1A 题
            if contest_id != 1 or problem_index != "A":
                continue

            # 检查是否是编译错误 (verdict = "COMPILATION_ERROR")
            verdict = sub.get("verdict")
            if verdict == "COMPILATION_ERROR":
                return True

        return False

    async def get_all_problems(self) -> Optional[List[Dict]]:
        """获取所有题目列表"""
        url = f"{Config.CF_API_URL}/problemset.problems"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    data = await resp.json()
                    if data["status"] == "OK":
                        return data["result"]["problems"]
                    return None
            except Exception as e:
                print(f"CF API错误: {e}")
                return None


    async def get_random_problem(
            self,
            min_rating: Optional[int] = 800,
            max_rating: Optional[int] = 5000,
            tags: Optional[List[str]] = None,
            exclude_solved: bool = False,
            user_qq: Optional[str] = None
    ) -> Optional[Dict]:
        """
        随机获取一道题目

        参数:
            min_rating: 最低难度（如 800）
            max_rating: 最高难度（如 2000）
            tags: 标签列表，如 ["dp", "greedy"]
            exclude_solved: 是否排除用户已解决的题目
            user_qq: 用户QQ（排除已解决时需要）
        """
        # 获取所有题目
        problems = await self.get_all_problems()
        if not problems:
            return None

        # 过滤题目
        filtered = []
        for p in problems:
            # 难度过滤
            rating = p.get("rating")
            if min_rating is not None and (rating is None or rating < min_rating):
                continue
            if max_rating is not None and (rating is not None and rating > max_rating):
                continue

            # 标签过滤
            if tags:
                problem_tags = set(p.get("tags", []))
                if not all(tag in problem_tags for tag in tags):
                    continue

            filtered.append(p)

        if not filtered:
            return None

        # 随机选择
        return random.choice(filtered)