import asyncio
import re
import time
from datetime import datetime, timedelta, timezone

import httpx


class CFDataService:
    def __init__(self):
        self._problemset_cache = []
        self._problemset_cache_ts = 0
        self._contest_cache = []
        self._contest_cache_ts = 0

    async def load_problemset(self) -> tuple[list[dict], str | None]:
        now = int(time.time())
        if self._problemset_cache and now - self._problemset_cache_ts < 1800:
            return self._problemset_cache, None

        url = "https://codeforces.com/api/problemset.problems"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            if self._problemset_cache:
                return self._problemset_cache, None
            return [], str(e)

        if data.get("status") != "OK":
            if self._problemset_cache:
                return self._problemset_cache, None
            return [], data.get("comment", "Codeforces API returned non-OK status")

        problems = data.get("result", {}).get("problems", [])
        self._problemset_cache = problems
        self._problemset_cache_ts = now
        return self._problemset_cache, None

    async def load_upcoming_contests(self) -> tuple[list[dict], str | None]:
        now = int(time.time())
        if self._contest_cache and now - self._contest_cache_ts < 300:
            return self._contest_cache, None

        contests: list[dict] = []
        errors: list[str] = []

        cf, cf_err = await self._fetch_codeforces_contests()
        if cf_err:
            errors.append(f"Codeforces: {cf_err}")
        contests.extend(cf)

        at, at_err = await self._fetch_atcoder_contests()
        if at_err:
            errors.append(f"AtCoder: {at_err}")
        contests.extend(at)

        nc, nc_err = await self._fetch_nowcoder_contests()
        if nc_err:
            errors.append(f"Nowcoder: {nc_err}")
        contests.extend(nc)

        contests.sort(key=lambda x: x["start_ts"])
        self._contest_cache = contests
        self._contest_cache_ts = now

        if contests:
            return contests, None
        return [], "; ".join(errors) if errors else "unknown error"

    async def fetch_profile_bundle(self, handle: str) -> tuple[dict | None, int, list[dict], str | None]:
        async with httpx.AsyncClient(timeout=20) as client:
            user_info_task = client.get(
                "https://codeforces.com/api/user.info",
                params={"handles": handle},
            )
            user_status_task = client.get(
                "https://codeforces.com/api/user.status",
                params={"handle": handle, "from": 1, "count": 10000},
            )
            try:
                info_resp, status_resp = await asyncio.gather(user_info_task, user_status_task)
                info_resp.raise_for_status()
                status_resp.raise_for_status()
                info_data = info_resp.json()
                status_data = status_resp.json()
            except Exception as e:
                return None, 0, [], str(e)

        if info_data.get("status") != "OK":
            return None, 0, [], info_data.get("comment", "Codeforces user.info returned non-OK status")
        if status_data.get("status") != "OK":
            return None, 0, [], status_data.get("comment", "Codeforces user.status returned non-OK status")

        users = info_data.get("result", [])
        if not users:
            return None, 0, [], "user not found"

        solved_ratings: dict[str, int | None] = {}
        for sub in status_data.get("result", []):
            if sub.get("verdict") != "OK":
                continue
            problem = sub.get("problem", {})
            cid = problem.get("contestId")
            idx = problem.get("index")
            if cid is None or not idx:
                continue
            key = f"{cid}{idx}"
            rating = self._safe_int(problem.get("rating"))
            if key not in solved_ratings:
                solved_ratings[key] = rating
            elif solved_ratings[key] is None and rating is not None:
                solved_ratings[key] = rating

        solved_dist = self._build_solved_rating_distribution(list(solved_ratings.values()))

        profile = users[0]
        if not isinstance(profile, dict):
            return None, 0, [], "invalid profile payload"

        return profile, len(solved_ratings), solved_dist, None

    def _build_solved_rating_distribution(self, ratings: list[int | None]) -> list[dict]:
        buckets = [
            {"id": "unrated", "label": "Unrated", "color": "#9ca3af", "min": None, "max": None},
            {"id": "lt1200", "label": "<1200", "color": "#808080", "min": 0, "max": 1199},
            {"id": "1200_1399", "label": "1200-1399", "color": "#00a000", "min": 1200, "max": 1399},
            {"id": "1400_1599", "label": "1400-1599", "color": "#03a89e", "min": 1400, "max": 1599},
            {"id": "1600_1899", "label": "1600-1899", "color": "#004dcc", "min": 1600, "max": 1899},
            {"id": "1900_2099", "label": "1900-2099", "color": "#aa00aa", "min": 1900, "max": 2099},
            {"id": "2100_2399", "label": "2100-2399", "color": "#ff8c00", "min": 2100, "max": 2399},
            {"id": "ge2400", "label": ">=2400", "color": "#d63131", "min": 2400, "max": None},
        ]
        counts = {b["id"]: 0 for b in buckets}

        for rating in ratings:
            bid = self._bucket_id_by_rating(rating)
            counts[bid] += 1

        result: list[dict] = []
        for b in buckets:
            result.append(
                {
                    "id": b["id"],
                    "label": b["label"],
                    "color": b["color"],
                    "count": counts[b["id"]],
                }
            )
        return result

    def _bucket_id_by_rating(self, rating: int | None) -> str:
        if rating is None:
            return "unrated"
        if rating < 1200:
            return "lt1200"
        if rating < 1400:
            return "1200_1399"
        if rating < 1600:
            return "1400_1599"
        if rating < 1900:
            return "1600_1899"
        if rating < 2100:
            return "1900_2099"
        if rating < 2400:
            return "2100_2399"
        return "ge2400"

    def _safe_int(self, value) -> int | None:
        try:
            return int(value)
        except Exception:
            return None

    async def _fetch_codeforces_contests(self) -> tuple[list[dict], str | None]:
        url = "https://codeforces.com/api/contest.list?gym=false"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [], str(e)

        if data.get("status") != "OK":
            return [], data.get("comment", "Codeforces API returned non-OK status")

        now = int(time.time())
        res = []
        for c in data.get("result", []):
            if c.get("phase") != "BEFORE":
                continue
            start_ts = int(c.get("startTimeSeconds", 0))
            if start_ts < now:
                continue
            cid = c.get("id")
            if cid is None:
                continue
            res.append(
                {
                    "site": "Codeforces",
                    "name": str(c.get("name", "Unknown Contest")),
                    "start_ts": start_ts,
                    "url": f"https://codeforces.com/contest/{cid}",
                }
            )
        return res, None

    async def _fetch_atcoder_contests(self) -> tuple[list[dict], str | None]:
        url = "https://atcoder.jp/contests/?lang=en"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            return [], str(e)

        pattern = re.compile(
            r'<time[^>]*>(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+0900)</time>.*?'
            r'<a href="(/contests/[^"]+)">([^<]+)</a>',
            re.S,
        )
        now_ts = int(time.time())
        res = []
        for m in pattern.finditer(html):
            dt_raw = m.group(1)
            href = m.group(2)
            name = re.sub(r"\s+", " ", m.group(3)).strip()
            try:
                dt = datetime.strptime(dt_raw, "%Y-%m-%d %H:%M:%S%z")
                start_ts = int(dt.timestamp())
            except Exception:
                continue
            if start_ts < now_ts:
                continue
            res.append(
                {
                    "site": "AtCoder",
                    "name": name,
                    "start_ts": start_ts,
                    "url": f"https://atcoder.jp{href}",
                }
            )
        return res, None

    async def _fetch_nowcoder_contests(self) -> tuple[list[dict], str | None]:
        url = "https://ac.nowcoder.com/acm/contest/vip-index"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            return [], str(e)

        now_ts = int(time.time())
        res = []
        json_pattern = re.compile(
            r'"contestId"\s*:\s*(\d+).*?"contestName"\s*:\s*"([^"]+)".*?'
            r'"startTime"\s*:\s*"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"',
            re.S,
        )
        for m in json_pattern.finditer(html):
            contest_id = m.group(1)
            name = self.unescape_html(m.group(2))
            dt_raw = m.group(3)
            start_ts = self.parse_cn_time_to_ts(dt_raw)
            if start_ts is None or start_ts < now_ts:
                continue
            res.append(
                {
                    "site": "Nowcoder",
                    "name": name,
                    "start_ts": start_ts,
                    "url": f"https://ac.nowcoder.com/acm/contest/{contest_id}",
                }
            )
        uniq = {}
        for c in res:
            uniq[c["url"]] = c
        return list(uniq.values()), None

    @staticmethod
    def parse_cn_time_to_ts(dt_raw: str) -> int | None:
        try:
            dt = datetime.strptime(dt_raw, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
        dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
        return int(dt.timestamp())

    @staticmethod
    def fmt_ts(ts: int) -> str:
        if not ts:
            return "-"
        dt = datetime.fromtimestamp(int(ts), tz=timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M (UTC+8)")

    @staticmethod
    def unescape_html(s: str) -> str:
        return (
            s.replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
