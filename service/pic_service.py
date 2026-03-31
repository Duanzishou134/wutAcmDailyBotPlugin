import os
import random
import shutil
import uuid

from astrbot.api.message_components import Image

class PicService:
    def __init__(self):
        # 获取插件根目录 (service 的上一级)
        self.plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pic_dir = os.path.join(self.plugin_dir, "pic")
        
        # 确保 pic 文件夹存在
        if not os.path.exists(self.pic_dir):
            os.makedirs(self.pic_dir)

    async def get_pic_list(self) -> str:
        """获取所有可用图片的列表文本（仅返回最后一个'-'之前的名称）"""
        images = self._get_images()
        if not images:
            return "目前没有任何图片。"

        names = set()
        for base, _ in images:
            head = base.rsplit("-", 1)[0] if "-" in base else base
            names.add(head)

        img_list = "\n".join(sorted(names))
        return f"可用的图片列表：\n{img_list}"

    async def get_pic_list_by_prefix(self, prefix: str) -> str:
        """获取指定前缀的图片列表（返回完整名称，不含扩展名）"""
        images = self._get_images()
        matches = [base for base, _ in images if base.startswith(prefix)]
        if not matches:
            return f"未找到以 {prefix} 为前缀的图片。"
        img_list = "\n".join(sorted(matches))
        return f"可用的图片列表：\n{img_list}"

    async def get_pic_path(self, pic_name: str) -> tuple[str, str | list[str] | None]:
        """按前缀规则匹配图片并返回结果"""
        images = self._get_images()
        candidates = [(base, path) for base, path in images if base.startswith(pic_name)]

        if not candidates:
            return "not_found", None

        exact_dash = [(base, path) for base, path in candidates if base.startswith(f"{pic_name}-")]
        if exact_dash:
            return "image", random.choice(exact_dash)[1]

        if len(candidates) == 1:
            return "image", candidates[0][1]

        conflict_names = sorted(base for base, _ in candidates)
        return "conflict", conflict_names

    def _get_images(self) -> list[tuple[str, str]]:
        exts = (".jpg", ".jpeg", ".gif", ".png")
        images: list[tuple[str, str]] = []
        for filename in os.listdir(self.pic_dir):
            lower = filename.lower()
            if not lower.endswith(exts):
                continue
            base, _ = os.path.splitext(filename)
            images.append((base, os.path.join(self.pic_dir, filename)))
        return images

    async def add_pic(self, pic_name: str, image: Image, add_suffix: bool) -> str:
        """将图片保存到 pic 目录，并返回结果提示文本"""
        source_path = await image.convert_to_file_path()
        size_bytes = os.path.getsize(source_path)
        if size_bytes >= 5 * 1024 * 1024:
            return "图片大小超过 5MB，无法添加。"
        ext = os.path.splitext(source_path)[1]
        if not ext:
            ext = ".jpg"

        if add_suffix:
            target_path = self._make_unique_path(pic_name, ext)
        else:
            target_path = os.path.join(self.pic_dir, f"{pic_name}{ext}")
            if os.path.exists(target_path):
                return f"图片 {pic_name}{ext} 已存在，请使用不同名称或去掉 -n。"

        shutil.copy2(source_path, target_path)
        return f"图片 {os.path.basename(target_path)} 添加成功！"

    def _make_unique_path(self, pic_name: str, ext: str) -> str:
        """生成带随机后缀的目标路径"""
        for _ in range(5):
            suffix = uuid.uuid4().hex[:6]
            filename = f"{pic_name}-{suffix}{ext}"
            target_path = os.path.join(self.pic_dir, filename)
            if not os.path.exists(target_path):
                return target_path
        filename = f"{pic_name}-{uuid.uuid4().hex}{ext}"
        return os.path.join(self.pic_dir, filename)