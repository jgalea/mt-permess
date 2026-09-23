"""Command-line interface for mt-permess."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import Any, Sequence, TextIO

from mt_permess import __version__
from mt_permess.client import DEFAULT_BASE, PermessClient, PermessError

# Named places for convenience (approx center lon, lat)
PLACES: dict[str, tuple[float, float]] = {
    "valletta": (14.5146, 35.8989),
    "sliema": (14.5042, 35.9126),
    "stjulians": (14.4899, 35.9197),
    "st-julians": (14.4899, 35.9197),
    "msida": (14.4890, 35.8970),
    "birkirkara": (14.4611, 35.8972),
    "mosta": (14.4256, 35.9092),
    "rabat": (14.3986, 35.8817),
    "mdina": (14.4031, 35.8869),
    "gozo": (14.2420, 36.0440),
    "victoria": (14.2397, 36.0444),
    "marsaskala": (14.5670, 35.8660),
    "zabbar": (14.5350, 35.8761),
    "zegbug": (14.4410, 35.8720),
    "attard": (14.4427, 35.8897),
    "naxxar": (14.4436, 35.9147),
    "gzira": (14.4940, 35.9058),
    "hamrun": (14.4894, 35.8860),
    "paola": (14.4980, 35.8730),
    "fgura": (14.5220, 35.8730),
    "birzebbuga": (14.5269, 35.8259),
    "mellieha": (14.3622, 35.9564),
    "stpauls": (14.4006, 35.9483),
    "st-pauls": (14.4006, 35.9483),
}


def main(argv: Sequence[str] | None = None) -> int:
    # A Windows console or pipe may not be UTF-8; print what it can rather than crash.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    try:
        return _main(argv)
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except Exception:
            pass
        return 0


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mt-permess",
        description="Malta planning permits CLI (permess.mt public API)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help=f"API base URL (default: {DEFAULT_BASE})",
    )
    parser.add_argument("--timeout", type=float, default=60.0)

    sub = parser.add_subparsers(dest="command", required=True)

    p_stats = sub.add_parser("stats", help="National permit totals and breakdowns")
    p_stats.add_argument("--start-year", type=int)
    p_stats.add_argument("--end-year", type=int)
    p_stats.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        dest="fmt",
    )

    p_near = sub.add_parser("near", help="Permits within a radius of a point")
    _add_location_args(p_near)
    p_near.add_argument(
        "--radius",
        type=float,
        default=300,
        help="Radius in metres (default: 300)",
    )
    p_near.add_argument(
        "--format",
        choices=("table", "json", "csv", "urls"),
        default="table",
        dest="fmt",
    )
    p_near.add_argument("--limit", type=int, help="Max rows to print")
    p_near.add_argument("-o", "--output", help="Write to file")

    p_area = sub.add_parser("area", help="Permits inside a bounding box")
    p_area.add_argument(
        "--nw",
        required=True,
        help='Northwest corner as "lon,lat" (e.g. "14.48,35.92")',
    )
    p_area.add_argument(
        "--se",
        required=True,
        help='Southeast corner as "lon,lat" (e.g. "14.52,35.89")',
    )
    p_area.add_argument("--start-year", type=int)
    p_area.add_argument("--end-year", type=int)
    p_area.add_argument("--year", type=int)
    p_area.add_argument("--type", dest="permit_type", help="Permit type filter (PA, DS, ...)")
    p_area.add_argument("--village", action="append", dest="villages")
    p_area.add_argument("--ai-category")
    p_area.add_argument("--ai-value")
    p_area.add_argument(
        "--format",
        choices=("table", "json", "csv", "urls"),
        default="table",
        dest="fmt",
    )
    p_area.add_argument("--limit", type=int)
    p_area.add_argument("-o", "--output")

    p_heatmap = sub.add_parser("heatmap", help="Grid heatmap counts")
    p_heatmap.add_argument("--start-year", type=int)
    p_heatmap.add_argument("--end-year", type=int)
    p_heatmap.add_argument("--type", dest="permit_type")
    p_heatmap.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        dest="fmt",
    )
    p_heatmap.add_argument("--top", type=int, default=20, help="Top cells to show in table")

    p_weekly = sub.add_parser("weekly", help="Weekly stats for a bounding box")
    p_weekly.add_argument("--nw", required=True, help='Northwest "lon,lat"')
    p_weekly.add_argument("--se", required=True, help='Southeast "lon,lat"')
    p_weekly.add_argument("--year", type=int)
    p_weekly.add_argument("--type", dest="permit_type")
    p_weekly.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        dest="fmt",
    )

    p_filters = sub.add_parser("filters", help="List AI category filters")
    p_filters.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        dest="fmt",
    )

    p_places = sub.add_parser("places", help="List built-in place shortcuts for near")
    p_places.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        dest="fmt",
    )

    args = parser.parse_args(argv)
    client = PermessClient(base_url=args.base_url, timeout=args.timeout)

    try:
        if args.command == "stats":
            return cmd_stats(client, args)
        if args.command == "near":
            return cmd_near(client, args)
        if args.command == "area":
            return cmd_area(client, args)
        if args.command == "heatmap":
            return cmd_heatmap(client, args)
        if args.command == "weekly":
            return cmd_weekly(client, args)
        if args.command == "filters":
            return cmd_filters(client, args)
        if args.command == "places":
            return cmd_places(args)
    except PermessError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130

    parser.error(f"unknown command: {args.command}")
    return 2


def _add_location_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--place", help="Named place (see: mt-permess places)")
    p.add_argument(
        "--latlon",
        help='Center as "lat,lon" (e.g. "35.90,14.51")',
    )
    p.add_argument("--lat", type=float, help="Latitude (use with --lon)")
    p.add_argument("--lon", type=float, help="Longitude (use with --lat)")


def resolve_latlon(args: argparse.Namespace) -> tuple[float, float]:
    if args.place:
        key = args.place.strip().lower().replace(" ", "").replace("'", "")
        key = key.replace("saint", "st").replace("ħ", "h").replace("ż", "z").replace("ġ", "g")
        if key not in PLACES:
            for name in PLACES:
                if key in name or name in key:
                    lon, lat = PLACES[name]
                    return lat, lon
            known = ", ".join(sorted(PLACES))
            raise PermessError(f"Unknown place {args.place!r}. Known: {known}")
        lon, lat = PLACES[key]
        return lat, lon

    if args.latlon:
        parts = [p.strip() for p in args.latlon.split(",")]
        if len(parts) != 2:
            raise PermessError('--latlon must be "lat,lon"')
        return float(parts[0]), float(parts[1])

    if args.lat is not None and args.lon is not None:
        return args.lat, args.lon

    raise PermessError("Provide --place, --latlon LAT,LON, or both --lat and --lon")


def cmd_stats(client: PermessClient, args: argparse.Namespace) -> int:
    data = client.stats(start_year=args.start_year, end_year=args.end_year)
    if args.fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    total = data.get("total_permits") or {}
    if isinstance(total, dict):
        total_n = total.get("count", total)
    else:
        total_n = total
    print(f"Total permits:          {total_n}")
    print(f"New last 7 days:        {data.get('new_permits_last_week')}")
    print(f"New last 30 days:       {data.get('new_permits_last_month')}")

    by_type = data.get("permits_by_type") or []
    if by_type:
        print("\nBy type:")
        for row in by_type[:15]:
            if isinstance(row, dict):
                print(f"  {row.get('type') or row.get('permit_type') or '?':<8} {row.get('count')}")
            else:
                print(f"  {row}")

    by_year = data.get("permits_by_year") or []
    recent = [r for r in by_year if isinstance(r, dict) and (r.get("year") or 0) >= 2015]
    if recent:
        print("\nBy year (since 2015):")
        for row in sorted(recent, key=lambda r: r.get("year") or 0, reverse=True)[:12]:
            print(f"  {row.get('year')}: {row.get('count')}")

    by_village = data.get("permits_by_village") or []
    if by_village:
        print("\nTop villages:")
        for row in by_village[:10]:
            if isinstance(row, dict):
                print(f"  {row.get('village') or row.get('name') or '?':<24} {row.get('count')}")
    return 0


def cmd_near(client: PermessClient, args: argparse.Namespace) -> int:
    lat, lon = resolve_latlon(args)
    data = client.radius(lat=lat, lon=lon, radius=args.radius)
    points = data.get("points") or []
    stats = data.get("stats") or {}

    if args.fmt == "json":
        payload = data
        if args.limit is not None:
            payload = {**data, "points": points[: args.limit]}
        return _emit(payload, args.output, raw_json=True)

    rows = [_point_row(p) for p in points]
    if args.limit is not None:
        rows = rows[: args.limit]

    if args.fmt == "urls":
        return _emit_urls(rows, args.output)

    if args.fmt == "csv":
        return _emit_csv(rows, args.output)

    print(
        f"# {stats.get('total_count', len(points))} permits within {args.radius:g}m "
        f"of {lat:.5f},{lon:.5f} (last 5y: {stats.get('last_5_years_count', '?')})",
        file=sys.stderr,
    )
    _print_table(rows, ["permit_year", "permit_type", "lat", "lon", "permit_url"])
    return 0


def cmd_area(client: PermessClient, args: argparse.Namespace) -> int:
    data = client.area(
        nw_lon_lat=_norm_lonlat(args.nw),
        se_lon_lat=_norm_lonlat(args.se),
        start_year=args.start_year,
        end_year=args.end_year,
        year=args.year,
        permit_type=args.permit_type,
        villages=args.villages,
        ai_category=args.ai_category,
        ai_value=args.ai_value,
    )
    permits = data.get("permits") or []
    count = data.get("count", len(permits))

    if args.fmt == "json":
        payload = data
        if args.limit is not None:
            payload = {**data, "permits": permits[: args.limit]}
        return _emit(payload, args.output, raw_json=True)

    rows = permits
    if args.limit is not None:
        rows = rows[: args.limit]

    if args.fmt == "urls":
        return _emit_urls(rows, args.output)

    if args.fmt == "csv":
        return _emit_csv(rows, args.output)

    print(
        f"# {count} permits in bbox (showing {len(rows)} detail rows)",
        file=sys.stderr,
    )
    cols = [
        "permit_number",
        "permit_type",
        "permit_year",
        "application_date",
        "address",
        "architect",
    ]
    _print_table(rows, cols)
    return 0


def cmd_heatmap(client: PermessClient, args: argparse.Namespace) -> int:
    data = client.heatmap(
        start_year=args.start_year,
        end_year=args.end_year,
        permit_type=args.permit_type,
    )
    if args.fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    grid = data.get("grid_counts") or {}
    print(f"Total: {data.get('total_count')}  max cell: {data.get('max_count')}  resolution: {data.get('resolution')}")
    print(f"Cells: {len(grid)}")
    top = sorted(grid.items(), key=lambda kv: kv[1], reverse=True)[: args.top]
    if top:
        print("\nTop cells:")
        for cell, n in top:
            print(f"  {cell:<16} {n}")
    return 0


def cmd_weekly(client: PermessClient, args: argparse.Namespace) -> int:
    data = client.weekly_area(
        nw_lon_lat=_norm_lonlat(args.nw),
        se_lon_lat=_norm_lonlat(args.se),
        year=args.year,
        permit_type=args.permit_type,
    )
    if args.fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_filters(client: PermessClient, args: argparse.Namespace) -> int:
    data = client.ai_filters()
    if args.fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    for item in data:
        if not isinstance(item, dict):
            print(item)
            continue
        vals = item.get("values") or []
        print(f"{item.get('id')}")
        print(f"  name:   {item.get('name')}")
        print(f"  values: {', '.join(str(v) for v in vals)}")
    return 0


def cmd_places(args: argparse.Namespace) -> int:
    items = [
        {"place": name, "lat": lat, "lon": lon}
        for name, (lon, lat) in sorted(PLACES.items())
    ]
    if args.fmt == "json":
        print(json.dumps(items, indent=2))
        return 0
    print(f"{'PLACE':<16} LAT       LON")
    print(f"{'-----':<16} ---       ---")
    for item in items:
        print(f"{item['place']:<16} {item['lat']:<9.4f} {item['lon']:<9.4f}")
    return 0


def _norm_lonlat(value: str) -> str:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 2:
        raise PermessError(f'Expected "lon,lat", got {value!r}')
    a, b = float(parts[0]), float(parts[1])
    # Accept lon,lat or lat,lon. Malta: lon ~14.x, lat ~35.x
    if 34.0 <= a <= 37.0 and 13.0 <= b <= 16.0:
        lon, lat = b, a  # lat,lon
    else:
        lon, lat = a, b  # lon,lat
    return f"{lon}, {lat}"


def _point_row(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "lat": p.get("lat"),
        "lon": p.get("lon"),
        "permit_year": p.get("permit_year"),
        "permit_type": p.get("permit_type"),
        "permit_url": p.get("permit_url"),
        "permit_number": p.get("permit_number"),
    }


def _print_table(rows: list[dict[str, Any]], cols: list[str]) -> None:
    if not rows:
        print("No results.")
        return
    present = [c for c in cols if any(c in r for r in rows)]
    if not present:
        present = list(rows[0].keys())
    widths = {c: len(c) for c in present}
    rendered: list[dict[str, str]] = []
    for row in rows:
        r = {c: _cell(row.get(c)) for c in present}
        rendered.append(r)
        for c in present:
            widths[c] = max(widths[c], min(len(r[c]), 48))
    print("  ".join(c.ljust(widths[c]) for c in present))
    print("  ".join("-" * widths[c] for c in present))
    for r in rendered:
        print("  ".join(r[c][: widths[c]].ljust(widths[c]) for c in present))


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _emit(data: Any, output: str | None, *, raw_json: bool = False) -> int:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


def _emit_urls(rows: list[dict[str, Any]], output: str | None) -> int:
    lines = [str(r.get("permit_url") or "") for r in rows if r.get("permit_url")]
    text = "\n".join(lines) + ("\n" if lines else "")
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


def _emit_csv(rows: list[dict[str, Any]], output: str | None) -> int:
    if not rows:
        if output:
            open(output, "w", encoding="utf-8").close()
            print(f"wrote {output}", file=sys.stderr)
        return 0
    keys: list[str] = []
    for row in rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    out: TextIO
    close = False
    if output:
        out = open(output, "w", encoding="utf-8", newline="")
        close = True
    else:
        out = sys.stdout
    try:
        writer = csv.DictWriter(out, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if close:
            out.close()
            print(f"wrote {output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
