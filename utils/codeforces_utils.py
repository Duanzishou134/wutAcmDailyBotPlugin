import aiohttp
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from ..config import Config


class CodeforcesUtils:

    async def get_user_submissions(self, codeforces_name: str, count: int = 10) -> Optional[List[Dict]]:
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