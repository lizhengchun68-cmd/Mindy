from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.common.paths import PROJECT_ROOT, resolve_path


@dataclass
class ProductDeclaration:
    style: str
    cn: str
    en: str
    unit_price: float
    unit_weight: float
    quantity: int
    hs_code: str
    category: str  # 服装 | 宠物


@dataclass
class Rules:
    raw: dict[str, Any]
    template_path: Path
    input_dir: Path
    output_dir: Path
    style_aliases: dict[str, str]
    clothing_styles: set[str]
    pet_styles: set[str]
    declarations: dict[str, ProductDeclaration]
    country_map: dict[str, str]
    country_cache_path: Path
    country_api_key_env: str
    country_case_insensitive: bool
    tail_columns: list[str]
    extra_header_template: list[str]
    builtin_slots: int = 3

    @classmethod
    def load(cls, rules_path: Path | None = None) -> Rules:
        rules_path = rules_path or PROJECT_ROOT / "config" / "rules.yaml"
        with open(rules_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        preset_file = resolve_path(raw["country_resolver"]["preset_map_file"])
        with open(preset_file, encoding="utf-8") as f:
            preset = yaml.safe_load(f)

        country_map: dict[str, str] = {}
        for section in ("north_america", "europe"):
            for name, code in preset.get(section, {}).items():
                country_map[str(name).strip()] = code

        declarations: dict[str, ProductDeclaration] = {}
        clothing_styles: set[str] = set()
        pet_styles: set[str] = set()
        for category, items in raw["product_declarations"].items():
            for item in items:
                decl = ProductDeclaration(category=category, **item)
                declarations[decl.style] = decl
                if category == "服装":
                    clothing_styles.add(decl.style)
                else:
                    pet_styles.add(decl.style)

        g = raw["global"]
        ext = raw["column_extension"]
        return cls(
            raw=raw,
            template_path=resolve_path(g["template"]),
            input_dir=resolve_path(g["input_dir"]),
            output_dir=resolve_path(g["output_dir"]),
            style_aliases=raw.get("style_aliases", {}),
            clothing_styles=clothing_styles,
            pet_styles=pet_styles,
            declarations=declarations,
            country_map=country_map,
            country_cache_path=resolve_path(raw["country_resolver"]["cache_file"]),
            country_api_key_env=raw["country_resolver"]["api_key_env"],
            country_case_insensitive=raw["country_resolver"].get("match_case_insensitive", True),
            tail_columns=ext["tail_columns"],
            extra_header_template=ext["header_template"],
            builtin_slots=ext.get("builtin_slots", 3),
        )

    def resolve_style(self, raw_style: str) -> str:
        s = (raw_style or "").strip()
        return self.style_aliases.get(s, s)

    def lookup_declaration(self, raw_style: str) -> ProductDeclaration:
        standard = self.resolve_style(raw_style)
        if standard not in self.declarations:
            raise KeyError(f"未知款式: {raw_style!r} -> {standard!r}")
        return self.declarations[standard]

    def style_category(self, raw_style: str) -> str:
        return self.lookup_declaration(raw_style).category
