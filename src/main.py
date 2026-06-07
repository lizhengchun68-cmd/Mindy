from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path

from src.common.config import Rules
from src.common.country import CountryResolver
from src.common.paths import PROJECT_ROOT
from src.reader.orders import group_by_order, list_input_files, read_orders
from src.transformer.headers import load_template_headers
from src.transformer.transform import TransformError, transform_groups
from src.writer.output import get_output_path, write_output


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y%m%d").date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mindy: 订单 xlsx → 顺丰模板")
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "rules.yaml")
    parser.add_argument("--input", type=Path, help="单个输入文件")
    parser.add_argument("--date", type=str, help="输出日期 YYYYMMDD，默认今天")
    parser.add_argument("--dry-run", action="store_true", help="只读取转换，不写文件")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    log = logging.getLogger("mindy")

    rules = Rules.load(args.config)
    run_date = parse_date(args.date) if args.date else date.today()
    template_headers = load_template_headers(rules.template_path)
    country_resolver = CountryResolver(rules)

    if args.input:
        input_files = [args.input]
    else:
        input_files = list_input_files(rules.input_dir)

    if not input_files:
        log.error("未找到输入 xlsx 文件")
        return 1

    all_rows = []
    for f in input_files:
        log.info("Processing: %s", f)
        all_rows.extend(read_orders(f))

    groups = group_by_order(all_rows)
    log.info("Input rows: %d, unique orders: %d", len(all_rows), len(groups))

    try:
        output_rows = transform_groups(groups, rules, country_resolver, run_date)
    except TransformError as e:
        log.error("%s", e)
        return 1

    for row in output_rows:
        log.info(
            "Order %s: A=%s B=%s E=%s products=%d",
            row.order_id.split("-")[-1],
            row.business_type,
            row.order_id,
            row.country_code,
            len(row.products),
        )

    if args.dry_run:
        log.info("Dry-run complete, %d output rows", len(output_rows))
        return 0

    output_path = get_output_path(rules.output_dir, run_date)
    log.info("Output target: %s", output_path)

    written, skipped = write_output(
        output_path,
        output_rows,
        rules,
        template_headers,
        append=output_path.exists(),
    )
    if skipped:
        log.info("Skipped %d duplicate order(s): %s", len(skipped), ", ".join(skipped))
    log.info("Written %d rows to %s", written, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
