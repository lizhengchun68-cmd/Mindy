from datetime import date

from src.common.config import Rules
from src.common.country import CountryResolver
from src.common.models import OrderRow
from src.reader.orders import group_by_order
from src.transformer.headers import build_headers, load_template_headers, row_to_values
from src.transformer.transform import TransformError, transform_groups


def _rules():
    return Rules.load()


def _row(order_no: str, style: str = "T恤", country: str = "Canada", **kwargs) -> OrderRow:
    return OrderRow(
        order_no=order_no,
        style=style,
        quantity=1,
        contact=kwargs.get("contact", "1234567890"),
        recipient=kwargs.get("recipient", "Test User"),
        country=country,
        city=kwargs.get("city", "Toronto"),
        state=kwargs.get("state", "ON"),
        zip_code=kwargs.get("zip_code", "M5V"),
        address=kwargs.get("address", "123 Main St"),
        source_row=kwargs.get("source_row", 1),
    )


def test_style_alias():
    rules = _rules()
    assert rules.resolve_style("短袖") == "T恤"
    assert rules.resolve_style("老爹帽") == "棒球帽"


def test_order_id_format():
    rules = _rules()
    resolver = CountryResolver(rules)
    groups = [[_row("12345", style="T恤")]]
    out = transform_groups(groups, rules, resolver, date(2026, 6, 6))[0]
    assert out.order_id == "E-0606-12345"


def test_us_business_type():
    rules = _rules()
    resolver = CountryResolver(rules)
    groups = [[_row("999", country="United States")]]
    out = transform_groups(groups, rules, resolver, date(2026, 6, 6))[0]
    assert out.business_type == "服装专线"
    assert out.country_code == "US"


def test_non_us_business_type():
    rules = _rules()
    resolver = CountryResolver(rules)
    groups = [[_row("999", country="France")]]
    out = transform_groups(groups, rules, resolver, date(2026, 6, 6))[0]
    assert out.business_type == "国际电商专递CD（普货）"


def test_merge_duplicate_orders():
    rules = _rules()
    resolver = CountryResolver(rules)
    rows = [
        _row("4069983558", style="T恤", source_row=1),
        _row("4069983558", style="棒球帽", source_row=2),
        _row("4069983558", style="带帽卫衣", source_row=3),
        _row("4069983558", style="圆领衫", source_row=4),
    ]
    groups = group_by_order(rows)
    assert len(groups) == 1
    out = transform_groups(groups, rules, resolver, date(2026, 6, 6))[0]
    assert len(out.products) == 4


def test_mixed_category_rejected():
    rules = _rules()
    resolver = CountryResolver(rules)
    rows = [
        _row("mix", style="T恤", source_row=1),
        _row("mix", style="PU宠物项圈", source_row=2),
    ]
    try:
        transform_groups(group_by_order(rows), rules, resolver)
        assert False, "expected TransformError"
    except TransformError:
        pass


def test_four_product_column_expansion():
    rules = _rules()
    template_headers = load_template_headers(rules.template_path)
    headers = build_headers(4, template_headers, rules)
    assert len(headers) == 97
    assert any(h == "英文申报品名4" for h in headers)


def test_remark_not_in_output():
    rules = _rules()
    resolver = CountryResolver(rules)
    template_headers = load_template_headers(rules.template_path)
    groups = [[_row("1", remark="secret note")]]
    out = transform_groups(groups, rules, resolver, date(2026, 6, 6))[0]
    vals = row_to_values(out, template_headers, rules)
    assert "secret note" not in vals
    assert "备注" not in template_headers
