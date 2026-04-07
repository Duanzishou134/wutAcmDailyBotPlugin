import os
import random
import shutil
import hashlib
import uuid

from astrbot.api.message_components import Image

class PicService:
    HASH_MOD = 1_000_000_007

    def __init__(self):
        # 获取插件根目录 (service 的上一级)
        self.plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pic_dir = os.path.join(self.plugin_dir, "pic")
        self.migration_flag = os.path.join(self.pic_dir, ".hash_mod_migration_done")
        
        # 确保 pic 文件夹存在
        if not os.path.exists(self.pic_dir):
            os.makedirs(self.pic_dir)

        self._migrate_pic_library_once()

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

        image_hash = self._hash_file(source_path)
        existing = self._find_existing_by_hash(image_hash)
        if existing:
            existing_name = os.path.splitext(os.path.basename(existing))[0]
            return f"已存在该图片，图片名称为 {existing_name}。"

        ext = os.path.splitext(source_path)[1]
        if not ext:
            ext = ".jpg"

        target_name = f"{pic_name}-{image_hash}{ext}"
        target_path = os.path.join(self.pic_dir, target_name)

        if add_suffix:
            if os.path.exists(target_path):
                return f"已存在该图片，图片名称为 {pic_name}-{image_hash}。"
        else:
            prefix = f"{pic_name}-"
            has_same_name = any(
                base.startswith(prefix)
                for base, _ in self._get_images()
            )
            if has_same_name:
                return f"图片名称 {pic_name} 已存在，请使用不同名称或去掉 -n。"

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

    def _hash_file(self, file_path: str) -> str:
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha.update(chunk)
        hash_num = int(sha.hexdigest(), 16) % self.HASH_MOD
        return str(hash_num)

    def _find_existing_by_hash(self, image_hash: str) -> str | None:
        target_hash = int(image_hash)
        for _, path in self._get_images():
            base = os.path.splitext(os.path.basename(path))[0]
            suffix = self._extract_hash_suffix(base)
            if suffix is not None and suffix == target_hash:
                return path

        for _, path in self._get_images():
            base = os.path.splitext(os.path.basename(path))[0]
            suffix = self._extract_hash_suffix(base)
            if suffix is not None:
                continue
            if self._hash_file(path) == image_hash:
                return path
        return None

    def _extract_hash_suffix(self, base_name: str) -> int | None:
        if "-" not in base_name:
            return None
        suffix = base_name.rsplit("-", 1)[1].lower()

        if suffix.isdigit():
            return int(suffix)

        # 兼容旧格式：64位十六进制 sha256 后缀
        if len(suffix) == 64 and all(c in "0123456789abcdef" for c in suffix):
            return int(suffix, 16) % self.HASH_MOD

        return None

    def _strip_legacy_or_hash_suffix(self, base_name: str) -> str:
        if "-" not in base_name:
            return base_name

        head, tail = base_name.rsplit("-", 1)
        lower_tail = tail.lower()
        is_legacy_suffix = len(lower_tail) == 6 and all(
            c in "0123456789abcdef" for c in lower_tail
        )
        is_mod_hash_suffix = lower_tail.isdigit()
        is_hash_suffix = len(lower_tail) == 64 and all(
            c in "0123456789abcdef" for c in lower_tail
        )
        if is_legacy_suffix or is_hash_suffix or is_mod_hash_suffix:
            return head
        return base_name

    def _migrate_pic_library_once(self) -> None:
        if os.path.exists(self.migration_flag):
            return

        exts = (".jpg", ".jpeg", ".gif", ".png")
        hash_to_path: dict[str, str] = {}

        for filename in os.listdir(self.pic_dir):
            lower = filename.lower()
            if not lower.endswith(exts):
                continue

            old_path = os.path.join(self.pic_dir, filename)
            base, ext = os.path.splitext(filename)
            pic_hash = self._hash_file(old_path)

            if pic_hash in hash_to_path:
                try:
                    os.remove(old_path)
                except OSError:
                    pass
                continue

            logical_name = self._strip_legacy_or_hash_suffix(base)
            new_filename = f"{logical_name}-{pic_hash}{ext}"
            new_path = os.path.join(self.pic_dir, new_filename)

            if old_path != new_path:
                if os.path.exists(new_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass
                else:
                    os.replace(old_path, new_path)

            hash_to_path[pic_hash] = new_path if os.path.exists(new_path) else old_path

        with open(self.migration_flag, "w", encoding="utf-8") as f:
            f.write("done")