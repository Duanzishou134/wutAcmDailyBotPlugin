import os
import base64
from datetime import datetime, timedelta, timezone

import httpx

from ..utils.html_render import render_template_to_image


class CFProfileCardService:
    def __init__(self, plugin_dir: str):
        self._card_dir = os.path.join(plugin_dir, "data", "cards")
        os.makedirs(self._card_dir, exist_ok=True)
        template_path = os.path.join(plugin_dir, "asserts", "cf_profile_card_template.html")
        self._template = self._load_template(template_path)

    async def render_profile_card(
        self,
        profile: dict | None,
        solved_count: int,
        solved_rating_dist: list[dict] | None = None,
    ) -> tuple[str | None, str | None]:
        if not isinstance(profile, dict) or not profile:
            return None, "empty profile data"

        rating = profile.get("rating")
        theme = self._rating_theme(rating)
        accent = theme["accent"]
        max_theme = self._rating_theme(self._safe_int(profile.get("maxRating")))

        handle = str(profile.get("handle", "unknown"))
        rank = str(profile.get("rank", "unrated"))
        max_rank = str(profile.get("maxRank", "-"))
        rating_text = str(profile.get("rating", "-"))
        max_rating = profile.get("maxRating", "-")
        friend_count = profile.get("friendOfCount", 0)
        contribution = profile.get("contribution", 0)
        country = str(profile.get("country", "-"))
        city = str(profile.get("city", "-"))
        org = str(profile.get("organization", "-"))
        reg_at = self._fmt_ts(profile.get("registrationTimeSeconds", 0)) if profile.get("registrationTimeSeconds") else "-"
        last_online = self._fmt_ts(profile.get("lastOnlineTimeSeconds", 0)) if profile.get("lastOnlineTimeSeconds") else "-"
        org_short = self._truncate(org, 36)
        country_city = self._truncate(f"{city}, {country}".strip(", "), 40)
        avatar_data_url = await self._load_avatar_data_url(profile.get("titlePhoto"))
        chart_bins, pie_gradient, solved_total = self._build_pie_chart_data(solved_rating_dist or [], solved_count)

        try:
            html_data = {
                "theme_name": theme["name"],
                "accent": self._rgb_to_css(accent),
                "accent_soft": self._rgb_to_css(theme["accent_soft"]),
                "bg_top": self._rgb_to_css(theme["bg_top"]),
                "bg_bottom": self._rgb_to_css(theme["bg_bottom"]),
                "handle": self._truncate(handle, 24),
                "rank": rank,
                "rating_text": rating_text,
                "max_rank": max_rank,
                "max_rating": str(max_rating),
                "max_accent": self._rgb_to_css(max_theme["accent"]),
                "solved_count": str(solved_count),
                "friend_count": str(friend_count),
                "contribution": str(contribution),
                "country_city": country_city,
                "organization": org_short,
                "last_online": last_online,
                "registered": reg_at,
                "short_last_online": self._fmt_ts_short(profile.get("lastOnlineTimeSeconds", 0)),
                "short_registered": self._fmt_ts_short(profile.get("registrationTimeSeconds", 0)),
                "avatar_data_url": avatar_data_url,
                "solved_rating_bins": chart_bins,
                "pie_gradient": pie_gradient,
                "solved_total": solved_total,
            }
            out_path = await render_template_to_image(
                self._template,
                html_data,
                width=1160,
                height=680,
                full_page=True,
                image_type="png",
            )
        except Exception as e:
            return None, str(e)
        return out_path, None

    def _rating_theme(self, rating: int | None) -> dict:
        if rating is None:
            return {"name": "Unrated Gray", "accent": (128, 128, 128), "accent_soft": (236, 236, 236), "bg_top": (245, 247, 251), "bg_bottom": (236, 240, 247)}
        if rating < 1200:
            return {"name": "Newbie Gray", "accent": (128, 128, 128), "accent_soft": (236, 236, 236), "bg_top": (246, 247, 249), "bg_bottom": (236, 239, 244)}
        if rating < 1400:
            return {"name": "Pupil Green", "accent": (0, 140, 0), "accent_soft": (219, 241, 219), "bg_top": (245, 251, 245), "bg_bottom": (232, 244, 232)}
        if rating < 1600:
            return {"name": "Specialist Cyan", "accent": (3, 168, 158), "accent_soft": (217, 240, 242), "bg_top": (243, 251, 252), "bg_bottom": (230, 244, 246)}
        if rating < 1900:
            return {"name": "Expert Blue", "accent": (0, 77, 204), "accent_soft": (218, 230, 253), "bg_top": (244, 248, 255), "bg_bottom": (231, 239, 252)}
        if rating < 2100:
            return {"name": "CM Purple", "accent": (170, 0, 170), "accent_soft": (237, 217, 246), "bg_top": (252, 245, 255), "bg_bottom": (243, 232, 250)}
        if rating < 2400:
            return {"name": "Master Orange", "accent": (255, 140, 0), "accent_soft": (252, 232, 209), "bg_top": (255, 249, 242), "bg_bottom": (250, 240, 227)}
        return {"name": "Grandmaster Red", "accent": (214, 49, 49), "accent_soft": (248, 219, 219), "bg_top": (255, 245, 245), "bg_bottom": (250, 233, 233)}

    def _truncate(self, text: str, limit: int) -> str:
        if text is None:
            return "-"
        s = str(text).strip()
        if len(s) <= limit:
            return s
        return s[: max(0, limit - 1)] + "…"

    def _rgb_to_css(self, color: tuple[int, int, int]) -> str:
        return f"rgb({color[0]}, {color[1]}, {color[2]})"

    async def _load_avatar_data_url(self, photo_url: str | None) -> str:
        if not photo_url:
            return self._default_avatar_data_url()
        url = str(photo_url).strip()
        if url.startswith("//"):
            url = "https:" + url
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            mime = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            if not mime.startswith("image/"):
                mime = "image/jpeg"
            encoded = base64.b64encode(resp.content).decode("ascii")
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return self._default_avatar_data_url()

    def _default_avatar_data_url(self) -> str:
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220" viewBox="0 0 220 220">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0%" stop-color="#334155"/><stop offset="100%" stop-color="#1e293b"/>'
            "</linearGradient></defs>"
            '<rect width="220" height="220" fill="url(#g)"/>'
            '<circle cx="110" cy="82" r="40" fill="#93c5fd"/>'
            '<rect x="58" y="128" width="104" height="72" rx="36" fill="#93c5fd"/>'
            "</svg>"
        )
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    def _load_template(self, template_path: str) -> str:
        with open(template_path, "r", encoding="utf-8") as file:
            return file.read()

    def _safe_int(self, v) -> int | None:
        try:
            return int(v)
        except Exception:
            return None

    def _fmt_ts(self, ts: int) -> str:
        if not ts:
            return "-"
        dt = datetime.fromtimestamp(int(ts), tz=timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M (UTC+8)")

    def _fmt_ts_short(self, ts: int) -> str:
        if not ts:
            return "-"
        dt = datetime.fromtimestamp(int(ts), tz=timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M")

    def _build_pie_chart_data(self, bins: list[dict], solved_count: int) -> tuple[list[dict], str, int]:
        prepared: list[dict] = []
        total = 0
        for item in bins:
            count = self._safe_int(item.get("count")) or 0
            total += count
            prepared.append(
                {
                    "label": str(item.get("label", "Unknown")),
                    "color": str(item.get("color", "#94a3b8")),
                    "count": count,
                    "percent": "0.0",
                }
            )

        if total <= 0:
            total = max(0, self._safe_int(solved_count) or 0)

        if not prepared:
            prepared = [{"label": "No data", "color": "#cbd5e1", "count": total, "percent": "100.0"}]
            return prepared, "#cbd5e1 0% 100%", total

        if total <= 0:
            for item in prepared:
                item["percent"] = "0.0"
            return prepared, "#e2e8f0 0% 100%", 0

        segments: list[str] = []
        cursor = 0.0
        non_zero_exists = False
        for item in prepared:
            count = item["count"]
            percent = (count / total) * 100
            item["percent"] = f"{percent:.1f}"
            if count <= 0:
                continue
            non_zero_exists = True
            end = cursor + percent
            segments.append(f"{item['color']} {cursor:.2f}% {end:.2f}%")
            cursor = end

        if not non_zero_exists:
            return prepared, "#e2e8f0 0% 100%", total

        if cursor < 100:
            segments.append(f"#f8fafc {cursor:.2f}% 100%")
        return prepared, ", ".join(segments), total
