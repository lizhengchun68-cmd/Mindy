from __future__ import annotations

import json
import os
from pathlib import Path

from src.common.config import Rules


class CountryResolver:
    def __init__(self, rules: Rules):
        self.rules = rules
        self._cache: dict[str, str] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        path = self.rules.country_cache_path
        if path.exists():
            with open(path, encoding="utf-8") as f:
                self._cache = json.load(f)

    def _save_cache(self) -> None:
        path = self.rules.country_cache_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def _normalize_key(self, name: str) -> str:
        key = (name or "").strip()
        if self.rules.country_case_insensitive:
            return key.casefold()
        return key

    def _lookup_preset(self, country_name: str) -> str | None:
        key = self._normalize_key(country_name)
        for map_key, code in self.rules.country_map.items():
            cmp_key = map_key.casefold() if self.rules.country_case_insensitive else map_key
            if cmp_key == key:
                return code
        return None

    def _lookup_cache(self, country_name: str) -> str | None:
        key = self._normalize_key(country_name)
        for map_key, code in self._cache.items():
            cmp_key = map_key.casefold() if self.rules.country_case_insensitive else map_key
            if cmp_key == key:
                return code
        return None

    def _deepseek(self, country_name: str) -> str:
        api_key = os.environ.get(self.rules.country_api_key_env)
        if not api_key:
            raise RuntimeError(
                f"国家 {country_name!r} 不在预置表中，且未设置 {self.rules.country_api_key_env}"
            )
        import httpx

        prompt = (
            "将以下国家/地区名称转换为 ISO 3166-1 alpha-2 两位代码，仅返回代码。\n"
            f"输入：{country_name}\n输出："
        )
        resp = httpx.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        code = text.split()[0].upper()
        if len(code) != 2:
            raise ValueError(f"DeepSeek 返回无效国家代码: {text!r}")
        return code

    def resolve(self, country_name: str) -> str:
        if not country_name or not str(country_name).strip():
            raise ValueError("收件人国家为空")

        preset = self._lookup_preset(country_name)
        if preset:
            return preset

        cached = self._lookup_cache(country_name)
        if cached:
            return cached

        code = self._deepseek(country_name)
        self._cache[country_name.strip()] = code
        self._save_cache()
        return code
