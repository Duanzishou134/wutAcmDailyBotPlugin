import os
import time
from datetime import datetime, timedelta, timezone

import httpx
from PIL import Image, ImageDraw, ImageFont, ImageOps


class CFProfileCardService:
    def __init__(self, plugin_dir: str):
        self._card_dir = os.path.join(plugin_dir, "data", "cards")
        os.makedirs(self._card_dir, exist_ok=True)

    async def render_profile_card(self, profile: dict, solved_count: int) -> tuple[str | None, str | None]:
        width, height = 1100, 620
        rating = profile.get("rating")
        theme = self._rating_theme(rating)
        bg_top = theme["bg_top"]
        bg_bottom = theme["bg_bottom"]
        accent = theme["accent"]
        accent_soft = theme["accent_soft"]

        canvas = Image.new("RGB", (width, height), bg_top)
        draw = ImageDraw.Draw(canvas)
        for y in range(height):
            ratio = y / max(1, height - 1)
            r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * ratio)
            g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * ratio)
            b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        draw.rounded_rectangle((14, 14, width - 14, height - 14), radius=16, fill=(255, 255, 255), outline=(226, 231, 241), width=2)
        header_h = 146
        draw.rounded_rectangle((14, 14, width - 14, 14 + header_h), radius=16, fill=(246, 249, 253), outline=(226, 231, 241), width=2)
        draw.line((14, 14 + header_h, width - 14, 14 + header_h), fill=(226, 231, 241), width=2)
        draw.line((658, 14 + header_h, 658, height - 14), fill=(234, 239, 247), width=2)
        draw.ellipse((840, -80, 1220, 220), fill=accent_soft)

        title_font = self._load_font(37)
        badge_font = self._load_font(21, bold=True)
        sub_font = self._load_font(23)
        body_font = self._load_font(25, bold=True)
        small_font = self._load_font(19)
        tiny_font = self._load_font(15)
        rating_bold_font = self._load_font(36, bold=True)
        right_val_font = self._load_font(33, bold=True)

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

        avatar = await self._load_avatar(profile.get("titlePhoto"))
        avatar = ImageOps.fit(avatar, (108, 108))
        mask = Image.new("L", (108, 108), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.ellipse((0, 0, 107, 107), fill=255)
        canvas.paste(avatar, (40, 34), mask)
        draw.ellipse((36, 30, 152, 146), outline=accent, width=4)

        draw.text((170, 42), self._truncate(handle, 24), fill=accent, font=title_font)
        badge_text = rank.upper()
        badge_w = int(draw.textlength(badge_text, font=badge_font)) + 28
        badge_x = 170
        badge_y = 96
        draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + 34), radius=18, fill=accent)
        draw.text((badge_x + 14, badge_y + 5), badge_text, fill=(255, 255, 255), font=badge_font)

        box_x0, box_y0, box_x1, box_y1 = 670, 38, 1060, 100
        draw.rounded_rectangle((box_x0, box_y0, box_x1, box_y1), radius=30, fill=(255, 255, 255), outline=(200, 210, 226), width=2)
        label = "Contest rating:"
        label_x = box_x0 + 20
        label_y = box_y0 + 18
        draw.text((label_x, label_y), label, fill=(40, 57, 82), font=sub_font)
        label_w = int(draw.textlength(label, font=sub_font))
        score_x = label_x + label_w
        score_y = box_y0 + 19
        draw.text((score_x, score_y), rating_text, fill=accent, font=sub_font)
        score_w = int(draw.textlength(rating_text, font=sub_font))
        max_text = f"(max {max_rating})"
        max_x = score_x + score_w + 6
        max_y = box_y0 + 24
        draw.text((max_x, max_y), max_text, fill=(95, 112, 142), font=tiny_font)
        draw.text((170, 138), f"{country_city}  |  {org_short}", fill=(61, 79, 106), font=tiny_font)

        lx0, lx1 = 40, 640
        ly = 202
        draw.text((lx0, ly), "RATING", fill=(90, 117, 153), font=tiny_font)
        draw.text((lx1 - int(draw.textlength(rating_text, font=rating_bold_font)), ly - 12), rating_text, fill=accent, font=rating_bold_font)
        draw.line((lx0, ly + 40, lx1, ly + 40), fill=(232, 237, 246), width=1)

        draw.rounded_rectangle((lx0, ly + 56, lx1, ly + 144), radius=22, fill=self._mix_color((255, 255, 255), accent, 0.10))
        max_theme = self._rating_theme(self._safe_int(max_rating))
        max_accent = max_theme["accent"]
        left_text = "Max rating: "
        left_x = lx0 + 20
        left_y = ly + 86
        draw.text((left_x, left_y), left_text, fill=(43, 64, 95), font=small_font)
        left_w = int(draw.textlength(left_text, font=small_font))
        max_num = str(max_rating)
        draw.text((left_x + left_w, left_y), max_num, fill=max_accent, font=small_font)
        num_w = int(draw.textlength(max_num, font=small_font))
        draw.text((left_x + left_w + num_w + 6, left_y), f"({max_rank})", fill=max_accent, font=small_font)

        draw.text((lx0, ly + 170), "SOLVED", fill=(90, 117, 153), font=tiny_font)
        draw.text((lx1 - int(draw.textlength(str(solved_count), font=body_font)), ly + 166), str(solved_count), fill=(25, 41, 68), font=body_font)
        draw.line((lx0, ly + 210, lx1, ly + 210), fill=(232, 237, 246), width=1)

        draw.rounded_rectangle((lx0, ly + 228, lx0 + 220, ly + 274), radius=23, fill=(241, 245, 252))
        draw.text((lx0 + 20, ly + 242), f"Friend of: {friend_count}", fill=(30, 49, 78), font=small_font)
        draw.rounded_rectangle((lx0 + 234, ly + 228, lx0 + 520, ly + 274), radius=23, fill=(241, 245, 252))
        draw.text((lx0 + 254, ly + 242), f"Contribution: {contribution}", fill=(30, 49, 78), font=small_font)
        draw.rounded_rectangle((lx0, ly + 288, lx0 + 520, ly + 334), radius=23, fill=(241, 245, 252))
        draw.text((lx0 + 20, ly + 302), f"Last online: {last_online}", fill=(30, 49, 78), font=small_font)
        draw.rounded_rectangle((lx0, ly + 346, lx0 + 520, ly + 392), radius=23, fill=(241, 245, 252))
        draw.text((lx0 + 20, ly + 360), f"Registered: {reg_at}", fill=(30, 49, 78), font=small_font)

        rx0, rx1 = 678, 1058
        draw.rounded_rectangle((rx0, 182, rx1, 470), radius=26, fill=(250, 252, 255), outline=(232, 237, 246), width=2)
        short_last_online = self._fmt_ts_short(profile.get("lastOnlineTimeSeconds", 0))
        short_reg_at = self._fmt_ts_short(profile.get("registrationTimeSeconds", 0))
        rows = [
            ("USERNAME", handle),
            ("RANK", rank),
            ("RATING", rating_text),
            ("LAST VISIT", short_last_online),
            ("REGISTERED", short_reg_at),
        ]
        row_y = 214
        for idx, (k, v) in enumerate(rows):
            draw.text((rx0 + 24, row_y), k, fill=(93, 120, 155), font=tiny_font)
            val_color = accent if k in {"RANK", "RATING", "USERNAME"} else (23, 38, 63)
            v_text = self._truncate(v, 22)
            use_font = right_val_font if k == "RATING" else small_font
            v_w = int(draw.textlength(v_text, font=use_font))
            val_x = max(rx0 + 185, rx1 - 24 - v_w)
            val_y = row_y - 7 if k == "RATING" else row_y
            draw.text((val_x, val_y), v_text, fill=val_color, font=use_font)
            if idx != len(rows) - 1:
                draw.line((rx0 + 20, row_y + 32, rx1 - 20, row_y + 32), fill=(235, 240, 248), width=1)
            row_y += 50

        draw.rounded_rectangle((rx0, 486, rx1, 560), radius=20, fill=(244, 247, 253))
        draw.text((rx0 + 18, 513), f"Theme: {theme['name']}", fill=(112, 129, 157), font=tiny_font)
        draw.text((rx0 + 214, 513), "Data: Codeforces API", fill=(112, 129, 157), font=tiny_font)

        file_name = f"cf_info_{handle}_{int(time.time())}.png"
        out_path = os.path.join(self._card_dir, file_name)
        try:
            canvas.save(out_path, format="PNG")
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

    def _mix_color(self, c1: tuple[int, int, int], c2: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
        a = max(0.0, min(1.0, alpha))
        return (int(c1[0] * (1 - a) + c2[0] * a), int(c1[1] * (1 - a) + c2[1] * a), int(c1[2] * (1 - a) + c2[2] * a))

    async def _load_avatar(self, photo_url: str | None) -> Image.Image:
        if not photo_url:
            return self._default_avatar()
        url = str(photo_url).strip()
        if url.startswith("//"):
            url = "https:" + url
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            from io import BytesIO
            return Image.open(BytesIO(resp.content)).convert("RGB")
        except Exception:
            return self._default_avatar()

    def _default_avatar(self) -> Image.Image:
        img = Image.new("RGB", (170, 170), (39, 57, 112))
        d = ImageDraw.Draw(img)
        d.ellipse((28, 22, 142, 136), fill=(80, 105, 184))
        d.rectangle((44, 104, 126, 168), fill=(80, 105, 184))
        return img

    def _load_font(self, size: int, bold: bool = False) -> ImageFont.ImageFont:
        if bold:
            candidates = [
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/msyhbd.ttc",
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        else:
            candidates = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/msyh.ttc"]
        for p in candidates:
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
        return ImageFont.load_default()

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
