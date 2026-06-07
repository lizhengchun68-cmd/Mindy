from __future__ import annotations

from datetime import date, datetime

from src.common.config import Rules
from src.common.country import CountryResolver
from src.common.models import OrderRow, OutputRow, ProductSlot


class TransformError(Exception):
    pass


def transform_groups(
    groups: list[list[OrderRow]],
    rules: Rules,
    country_resolver: CountryResolver,
    run_date: date | None = None,
) -> list[OutputRow]:
    run_date = run_date or date.today()
    mmdd = run_date.strftime("%m%d")
    results: list[OutputRow] = []

    for group in groups:
        try:
            results.append(_transform_group(group, rules, country_resolver, mmdd))
        except (TransformError, KeyError, ValueError) as e:
            order_no = group[0].order_no if group else "?"
            raise TransformError(f"订单 {order_no} 转换失败: {e}") from e

    return results


def _transform_group(
    group: list[OrderRow],
    rules: Rules,
    country_resolver: CountryResolver,
    mmdd: str,
) -> OutputRow:
    if not group:
        raise TransformError("空订单组")

    head = group[0]
    categories = set()
    products: list[ProductSlot] = []

    for item in group:
        cat = rules.style_category(item.style)
        categories.add(cat)
        decl = rules.lookup_declaration(item.style)
        products.append(
            ProductSlot(
                en=decl.en,
                cn=decl.cn,
                unit_price=decl.unit_price,
                unit_weight=decl.unit_weight,
                quantity=decl.quantity,
                hs_code=decl.hs_code,
            )
        )

    if len(categories) > 1:
        raise TransformError("同一订单混有服装与宠物商品")

    prefix = (
        rules.raw["order_id_format"]["clothing_prefix"]
        if "服装" in categories
        else rules.raw["order_id_format"]["pet_prefix"]
    )
    order_id = f"{prefix}-{mmdd}-{head.order_no}"

    country_code = country_resolver.resolve(head.country or "")
    bt = rules.raw["business_type"]
    business_type = (
        bt["us_value"]
        if country_code in bt["us_country_codes"]
        else bt["default_value"]
    )

    contact = (head.contact or "").strip()
    phone = contact or rules.raw["contact_defaults"]["fallback_phone"]

    return OutputRow(
        business_type=business_type,
        order_id=order_id,
        contact_name=head.recipient or "",
        country_code=country_code,
        state=head.state or "",
        city=head.city or "",
        address=head.address or "",
        zip_code=str(head.zip_code or ""),
        phone=phone,
        products=products,
    )
