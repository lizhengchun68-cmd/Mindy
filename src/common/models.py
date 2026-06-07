from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OrderRow:
    order_no: str
    style: str
    quantity: str | int | float | None
    contact: str | None
    recipient: str | None
    country: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    address: str | None
    remark: str | None = None
    source_row: int = 0


@dataclass
class ProductSlot:
    en: str
    cn: str
    unit_price: float
    unit_weight: float
    quantity: int
    hs_code: str


@dataclass
class OutputRow:
    business_type: str
    order_id: str
    contact_name: str
    country_code: str
    state: str
    city: str
    address: str
    zip_code: str
    phone: str
    products: list[ProductSlot] = field(default_factory=list)
