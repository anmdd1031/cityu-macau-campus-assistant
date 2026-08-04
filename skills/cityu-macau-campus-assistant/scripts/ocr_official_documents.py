#!/usr/bin/env python3
"""OCR locally saved official-site PDFs and optional raster-image assets.

The script never sends network requests. It reads the content-addressed bodies
and SQLite state produced by ``crawl_official_sites.py``, renders one PDF page
or image at a time, runs local Chinese/English OCR serially, and writes a
resumable OCR cache consumed by ``audit_official_crawl.py``. Raster images are
opt-in because a complete site crawl can contain many decorative photographs.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
import urllib.parse

import numpy as np

try:
    import pypdfium2 as pdfium
except ImportError as error:  # pragma: no cover - exercised by operator setup
    raise SystemExit(
        "pypdfium2 is required; install scripts/requirements-ocr.txt"
    ) from error

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError as error:  # pragma: no cover - exercised by operator setup
    raise SystemExit(
        "rapidocr-onnxruntime is required; install scripts/requirements-ocr.txt"
    ) from error

try:
    from PIL import Image, ImageOps
except ImportError as error:  # pragma: no cover - exercised by operator setup
    raise SystemExit(
        "Pillow is required; install scripts/requirements-ocr.txt"
    ) from error

from audit_official_crawl import extract_pdf
from crawl_official_sites import AdvisoryProcessLock, now_beijing


def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    skill_root = script_path.parent.parent
    repository_root = skill_root.parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=repository_root / ".cache" / "cityu-official-crawl",
    )
    parser.add_argument(
        "--ocr-dir",
        type=Path,
        default=None,
        help="OCR cache; defaults to STATE_DIR/ocr",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.8,
        help="PDF render scale; default 1.8 (about 130 dpi)",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.35,
        help="Discard OCR lines below this confidence; default 0.35",
    )
    parser.add_argument(
        "--tile-height",
        type=int,
        default=4200,
        help="Split unusually tall rendered pages into tiles; default 4200 pixels",
    )
    parser.add_argument(
        "--tile-overlap",
        type=int,
        default=240,
        help="Vertical overlap between OCR tiles; default 240 pixels",
    )
    parser.add_argument(
        "--sha256",
        action="append",
        default=[],
        help="Only OCR this body digest; may be repeated",
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        default=None,
        help="Stop after this many documents; useful for a local smoke test",
    )
    parser.add_argument(
        "--include-images",
        action="store_true",
        help=(
            "Also OCR fetched JPEG/PNG/GIF/WebP/BMP/TIFF assets. This is local "
            "and serial but may take a long time on a complete crawl."
        ),
    )
    parser.add_argument(
        "--images-only",
        action="store_true",
        help="OCR raster images without scanning the PDF inventory",
    )
    parser.add_argument(
        "--min-image-bytes",
        type=int,
        default=1024,
        help="Ignore raster assets smaller than this many bytes; default 1024",
    )
    parser.add_argument(
        "--max-image-side",
        type=int,
        default=3600,
        help="Downscale long image edges above this size before OCR; default 3600",
    )
    parser.add_argument(
        "--min-image-text-characters",
        type=int,
        default=8,
        help=(
            "Record an image as text-bearing at or above this many visible OCR "
            "characters; smaller results are recorded as reviewed/no_text"
        ),
    )
    parser.add_argument(
        "--min-pdf-text-characters",
        type=int,
        default=20,
        help=(
            "Record OCR text for a scanned PDF as usable at or above this many "
            "visible characters; smaller results remain reviewed/no_text"
        ),
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Atomically save the OCR manifest every N processed assets; default 25",
    )
    parser.add_argument(
        "--directml",
        action="store_true",
        help=(
            "Use the Windows DirectML execution provider for OCR inference; "
            "requires onnxruntime-directml in the active environment"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild documents already recorded as successful",
    )
    return parser.parse_args()


class SingleProcessLock(AdvisoryProcessLock):
    """Prevent two expensive OCR passes from writing the same cache."""

    def __init__(self, path: Path) -> None:
        super().__init__(path, "OCR")


def load_manifest(path: Path) -> dict[str, dict[str, object]]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, list):
        return {}
    entries: dict[str, dict[str, object]] = {}
    for item in payload:
        if not isinstance(item, dict) or not item.get("sha256"):
            continue
        normalized = dict(item)
        # Manifests written before raster-image support only contained PDFs.
        normalized.setdefault("kind", "pdf")
        entries[str(normalized["sha256"])] = normalized
    return entries


def save_manifest(path: Path, entries: dict[str, dict[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            [entries[digest] for digest in sorted(entries)],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def fetched_content_digests(database: Path) -> set[str]:
    connection = sqlite3.connect(database)
    try:
        return {
            str(row[0])
            for row in connection.execute(
                """
                SELECT DISTINCT sha256
                FROM urls
                WHERE state='fetched' AND sha256 IS NOT NULL
                """
            )
        }
    finally:
        connection.close()


def pdf_inventory(database: Path) -> list[dict[str, object]]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT url, sha256, body_path, content_type, body_bytes
            FROM urls
            WHERE state = 'fetched'
              AND sha256 IS NOT NULL
              AND body_path IS NOT NULL
              AND (
                    lower(content_type) = 'application/pdf'
                 OR lower(url) LIKE '%.pdf'
                 OR lower(url) LIKE '%.pdf?%'
              )
            ORDER BY sha256, url
            """
        ).fetchall()
    finally:
        connection.close()

    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        url = str(row["url"])
        media_type = str(row["content_type"] or "").partition(";")[0].strip().lower()
        suffix = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).suffix.lower()
        if media_type not in {
            "",
            "application/octet-stream",
            "application/pdf",
            "application/x-pdf",
            "binary/octet-stream",
        }:
            continue
        if media_type not in {"application/pdf", "application/x-pdf"} and suffix != ".pdf":
            continue
        digest = str(row["sha256"])
        item = grouped.setdefault(
            digest,
            {
                "kind": "pdf",
                "sha256": digest,
                "body_path": str(row["body_path"]),
                "body_bytes": int(row["body_bytes"] or 0),
                "urls": [],
            },
        )
        urls = item["urls"]
        assert isinstance(urls, list)
        urls.append(url)
    return list(grouped.values())


RASTER_IMAGE_TYPES = {
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}
RASTER_IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def is_raster_image(url: str, content_type: str) -> bool:
    suffix = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).suffix.lower()
    media_type = content_type.partition(";")[0].strip().lower()
    if media_type:
        if media_type.startswith("image/"):
            return media_type in RASTER_IMAGE_TYPES
        if media_type not in {"application/octet-stream", "binary/octet-stream"}:
            return False
    return suffix in RASTER_IMAGE_SUFFIXES


def image_inventory(database: Path) -> list[dict[str, object]]:
    """Return fetched raster assets grouped by immutable response digest."""

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT url, sha256, body_path, content_type, body_bytes
            FROM urls
            WHERE state = 'fetched'
              AND sha256 IS NOT NULL
              AND body_path IS NOT NULL
              AND (
                    lower(content_type) LIKE 'image/%'
                 OR lower(url) LIKE '%.jpg'
                 OR lower(url) LIKE '%.jpg?%'
                 OR lower(url) LIKE '%.jpeg'
                 OR lower(url) LIKE '%.jpeg?%'
                 OR lower(url) LIKE '%.png'
                 OR lower(url) LIKE '%.png?%'
                 OR lower(url) LIKE '%.gif'
                 OR lower(url) LIKE '%.gif?%'
                 OR lower(url) LIKE '%.webp'
                 OR lower(url) LIKE '%.webp?%'
                 OR lower(url) LIKE '%.bmp'
                 OR lower(url) LIKE '%.bmp?%'
                 OR lower(url) LIKE '%.tif'
                 OR lower(url) LIKE '%.tif?%'
                 OR lower(url) LIKE '%.tiff'
                 OR lower(url) LIKE '%.tiff?%'
              )
            ORDER BY sha256, url
            """
        ).fetchall()
    finally:
        connection.close()

    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        url = str(row["url"])
        content_type = str(row["content_type"] or "")
        if not is_raster_image(url, content_type):
            continue
        digest = str(row["sha256"])
        item = grouped.setdefault(
            digest,
            {
                "kind": "image",
                "sha256": digest,
                "body_path": str(row["body_path"]),
                "body_bytes": int(row["body_bytes"] or 0),
                "content_type": content_type,
                "urls": [],
            },
        )
        urls = item["urls"]
        assert isinstance(urls, list)
        urls.append(url)
    return list(grouped.values())


def normalize_ocr_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip() + "\n"


def vertical_tile_offsets(height: int, tile_height: int, overlap: int) -> list[int]:
    if height <= tile_height:
        return [0]
    step = tile_height - overlap
    offsets = list(range(0, max(1, height - tile_height + 1), step))
    final_offset = height - tile_height
    if not offsets or offsets[-1] != final_offset:
        offsets.append(final_offset)
    return list(dict.fromkeys(offsets))


def ocr_rendered_page(
    engine: RapidOCR,
    image: object,
    image_path: Path,
    min_confidence: float,
    tile_height: int,
    tile_overlap: int,
    persist_input: bool = True,
) -> tuple[list[dict[str, object]], list[object]]:
    """OCR a rendered page, tiling tall posters and long screenshot PDFs."""

    width, height = image.size  # type: ignore[attr-defined]
    offsets = vertical_tile_offsets(height, tile_height, tile_overlap)
    records: list[dict[str, object]] = []
    elapsed_values: list[object] = []
    seen_positions: list[tuple[str, float]] = []
    for tile_index, top in enumerate(offsets, start=1):
        bottom = min(height, top + tile_height)
        if len(offsets) == 1:
            tile_path = image_path
            tile_image = image
        else:
            tile_path = image_path.with_name(
                f"{image_path.stem}-tile-{tile_index:03d}.png"
            )
            tile_image = image.crop(  # type: ignore[attr-defined]
                (0, top, width, bottom)
            )
        if persist_input and len(offsets) > 1:
            tile_image.save(tile_path, format="PNG", optimize=True)  # type: ignore[attr-defined]
        result, elapsed = engine(
            str(tile_path) if persist_input else np.asarray(tile_image)
        )
        elapsed_values.append(elapsed)
        for item in result or []:
            box, text, confidence = item
            value = str(text).strip()
            confidence_value = float(confidence)
            if confidence_value < min_confidence or not value:
                continue
            global_box = [
                [float(point[0]), float(point[1]) + top]
                for point in box
            ]
            vertical_position = sum(point[1] for point in global_box) / len(global_box)
            duplicate_overlap = any(
                previous_text == value
                and abs(previous_position - vertical_position) <= tile_overlap * 1.5
                for previous_text, previous_position in seen_positions[-80:]
            )
            if duplicate_overlap:
                continue
            seen_positions.append((value, vertical_position))
            records.append(
                {
                    "box": global_box,
                    "text": value,
                    "confidence": confidence_value,
                    "tile": tile_index,
                }
            )
    records.sort(
        key=lambda item: (
            sum(point[1] for point in item["box"]) / len(item["box"]),
            sum(point[0] for point in item["box"]) / len(item["box"]),
        )
    )
    return records, elapsed_values


def ocr_document(
    engine: RapidOCR,
    body: bytes,
    output_dir: Path,
    scale: float,
    min_confidence: float,
    tile_height: int,
    tile_overlap: int,
    force: bool,
) -> tuple[int, str, int, list[str]]:
    document = pdfium.PdfDocument(body)
    page_texts: list[str] = []
    resumed_pages = 0
    try:
        for page_index in range(len(document)):
            page_number = page_index + 1
            stem = f"page-{page_number:03d}"
            image_path = output_dir / f"{stem}.png"
            text_path = output_dir / f"{stem}.txt"
            json_path = output_dir / f"{stem}.json"
            if not force and text_path.is_file() and json_path.is_file():
                page_texts.append(
                    text_path.read_text(encoding="utf-8", errors="replace")
                )
                resumed_pages += 1
                print(f"OCR RESUME page={page_number}/{len(document)}", flush=True)
                continue

            page = document[page_index]
            try:
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil().convert("RGB")
                image.save(image_path, format="PNG", optimize=True)
            finally:
                page.close()

            started = time.perf_counter()
            records, elapsed = ocr_rendered_page(
                engine,
                image,
                image_path,
                min_confidence,
                tile_height,
                tile_overlap,
            )
            lines = [str(record["text"]) for record in records]
            page_text = "\n".join(lines).strip() + ("\n" if lines else "")
            text_path.write_text(page_text, encoding="utf-8")
            json_path.write_text(
                json.dumps(
                    {
                        "page": page_number,
                        "render_scale": scale,
                        "render_size": [image.width, image.height],
                        "tile_height": tile_height,
                        "tile_overlap": tile_overlap,
                        "engine_elapsed": elapsed,
                        "wall_seconds": round(time.perf_counter() - started, 3),
                        "lines": records,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            page_texts.append(page_text)
            print(
                f"OCR PAGE page={page_number}/{len(document)} lines={len(lines)}",
                flush=True,
            )
    finally:
        document.close()
    combined = "\n".join(
        f"--- page {index} ---\n{text.strip()}"
        for index, text in enumerate(page_texts, start=1)
    ).strip()
    return len(page_texts), combined, resumed_pages, []


def ocr_image_asset(
    engine: RapidOCR,
    body: bytes,
    output_dir: Path,
    min_confidence: float,
    tile_height: int,
    tile_overlap: int,
    max_image_side: int,
    force: bool,
) -> tuple[int, str, int, list[str]]:
    """Decode and OCR every frame/page of one locally stored raster asset."""

    image_texts: list[str] = []
    resumed_frames = 0
    decode_warnings: list[str] = []
    with Image.open(io.BytesIO(body)) as source:
        frame_count = int(getattr(source, "n_frames", 1) or 1)
        for frame_index in range(frame_count):
            frame_number = frame_index + 1
            stem = "image" if frame_count == 1 else f"frame-{frame_number:03d}"
            image_path = output_dir / f"{stem}.png"
            text_path = output_dir / f"{stem}.txt"
            json_path = output_dir / f"{stem}.json"
            if not force and text_path.is_file() and json_path.is_file():
                image_texts.append(
                    text_path.read_text(encoding="utf-8", errors="replace")
                )
                resumed_frames += 1
                print(
                    f"OCR RESUME image={frame_number}/{frame_count}",
                    flush=True,
                )
                continue

            try:
                source.seek(frame_index)
            except (EOFError, ValueError) as error:
                warning = (
                    f"frame {frame_number}/{frame_count} is not decodable: "
                    f"{type(error).__name__}: {error}"
                )
                decode_warnings.append(warning)
                print(
                    f"OCR FRAME_SKIPPED image={frame_number}/{frame_count} "
                    f"error={type(error).__name__}: {error}",
                    flush=True,
                )
                continue
            original_size = [int(source.width), int(source.height)]
            oriented = ImageOps.exif_transpose(source)
            if oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info:
                canvas = Image.new("RGBA", oriented.size, "white")
                canvas.alpha_composite(oriented.convert("RGBA"))
                image = canvas.convert("RGB")
            else:
                image = oriented.convert("RGB")
            if max(image.size) > max_image_side:
                image.thumbnail(
                    (max_image_side, max_image_side),
                    Image.Resampling.LANCZOS,
                )
            started = time.perf_counter()
            records, elapsed = ocr_rendered_page(
                engine,
                image,
                image_path,
                min_confidence,
                tile_height,
                tile_overlap,
                persist_input=False,
            )
            lines = [str(record["text"]) for record in records]
            if lines:
                image.save(image_path, format="PNG", optimize=False)
            image_text = "\n".join(lines).strip() + ("\n" if lines else "")
            text_path.write_text(image_text, encoding="utf-8")
            json_path.write_text(
                json.dumps(
                    {
                        "page": frame_number,
                        "frame_count": frame_count,
                        "original_size": original_size,
                        "render_size": [image.width, image.height],
                        "render_path": image_path.name if lines else None,
                        "max_image_side": max_image_side,
                        "tile_height": tile_height,
                        "tile_overlap": tile_overlap,
                        "engine_elapsed": elapsed,
                        "wall_seconds": round(time.perf_counter() - started, 3),
                        "lines": records,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            image_texts.append(image_text)
            print(
                f"OCR IMAGE image={frame_number}/{frame_count} lines={len(lines)}",
                flush=True,
            )
    combined = "\n".join(
        f"--- image {index} ---\n{text.strip()}"
        for index, text in enumerate(image_texts, start=1)
    ).strip()
    if not image_texts:
        raise ValueError("raster asset has no decodable image frame")
    return len(image_texts), combined, resumed_frames, decode_warnings


def main() -> int:
    args = parse_args()
    if args.scale <= 0:
        raise SystemExit("--scale must be positive")
    if not 0 <= args.min_confidence <= 1:
        raise SystemExit("--min-confidence must be between 0 and 1")
    if args.tile_height <= 0:
        raise SystemExit("--tile-height must be positive")
    if not 0 <= args.tile_overlap < args.tile_height:
        raise SystemExit("--tile-overlap must be non-negative and smaller than tile height")
    if args.max_documents is not None and args.max_documents <= 0:
        raise SystemExit("--max-documents must be positive")
    if args.min_image_bytes < 0:
        raise SystemExit("--min-image-bytes must be non-negative")
    if args.max_image_side <= 0:
        raise SystemExit("--max-image-side must be positive")
    if args.min_image_text_characters < 0:
        raise SystemExit("--min-image-text-characters must be non-negative")
    if args.min_pdf_text_characters < 0:
        raise SystemExit("--min-pdf-text-characters must be non-negative")
    if args.checkpoint_every <= 0:
        raise SystemExit("--checkpoint-every must be positive")

    state_dir = args.state_dir.resolve()
    database = state_dir / "crawl.sqlite3"
    if not database.is_file():
        raise SystemExit(f"Crawl database not found: {database}")
    ocr_dir = args.ocr_dir.resolve() if args.ocr_dir else state_dir / "ocr"
    ocr_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = ocr_dir / "manifest.json"
    selected_digests = {value.lower() for value in args.sha256}

    with SingleProcessLock(ocr_dir / "ocr.lock"):
        manifest = load_manifest(manifest_path)
        current_digests = fetched_content_digests(database)
        stale_digests = set(manifest) - current_digests
        for digest in stale_digests:
            del manifest[digest]
        inventory: list[dict[str, object]] = []
        if not args.images_only:
            inventory.extend(pdf_inventory(database))
        if args.include_images or args.images_only:
            inventory.extend(image_inventory(database))
        inventory.sort(
            key=lambda item: (
                0 if item["kind"] == "pdf" else 1,
                str(item["sha256"]),
            )
        )
        queue: list[tuple[dict[str, object], str]] = []
        manifest_changed = bool(stale_digests)
        for item in inventory:
            digest = str(item["sha256"])
            if selected_digests and digest.lower() not in selected_digests:
                continue
            body_path = state_dir / str(item["body_path"])
            if not body_path.is_file():
                continue
            kind = str(item["kind"])
            existing = manifest.get(digest, {})
            if kind == "image" and int(item["body_bytes"] or 0) < args.min_image_bytes:
                if args.force or existing.get("status") != "excluded_small":
                    urls = [str(value) for value in item["urls"]]
                    manifest[digest] = {
                        "sha256": digest,
                        "kind": kind,
                        "url": urls[0],
                        "duplicate_urls": urls[1:],
                        "body_path": str(item["body_path"]),
                        "status": "excluded_small",
                        "pages": 1,
                        "text_characters": 0,
                        "seconds": 0,
                        "error": None,
                        "source_issue": (
                            f"raster image is smaller than --min-image-bytes "
                            f"({int(item['body_bytes'] or 0)} < {args.min_image_bytes})"
                        ),
                        "generated_at": now_beijing(),
                    }
                    manifest_changed = True
                continue
            combined_path = ocr_dir / digest / "combined.normalized.txt"
            if (
                not args.force
                and existing.get("status") in {"success", "no_text"}
                and combined_path.is_file()
            ):
                continue
            if kind == "pdf":
                body = body_path.read_bytes()
                if hashlib.sha256(body).hexdigest() != digest:
                    manifest[digest] = {
                        "sha256": digest,
                        "kind": kind,
                        "url": str(item["urls"][0]),
                        "duplicate_urls": [str(value) for value in item["urls"][1:]],
                        "body_path": str(item["body_path"]),
                        "status": "failed",
                        "pages": None,
                        "text_characters": 0,
                        "seconds": 0,
                        "error": "cached response SHA-256 does not match its manifest digest",
                        "generated_at": now_beijing(),
                    }
                    manifest_changed = True
                    continue
                inspection = extract_pdf(body)
                issue = str(inspection.get("issue") or "")
                if not issue:
                    continue
            else:
                issue = "raster image requires local OCR review"
            queue.append((item, issue))

        if manifest_changed:
            save_manifest(manifest_path, manifest)

        if args.max_documents is not None:
            queue = queue[: args.max_documents]
        print(
            f"OCR QUEUE assets={len(queue)} inventory={len(inventory)} ",
            f"output={ocr_dir}",
            flush=True,
        )
        if not queue:
            return 0

        engine_options: dict[str, bool] = {}
        inference_provider = "CPUExecutionProvider"
        if args.directml:
            try:
                from onnxruntime import get_available_providers
            except ImportError as error:  # pragma: no cover - operator setup
                raise SystemExit(
                    "--directml requires onnxruntime-directml in the active environment"
                ) from error
            available_providers = get_available_providers()
            if "DmlExecutionProvider" not in available_providers:
                raise SystemExit(
                    "--directml requested but DmlExecutionProvider is unavailable; "
                    f"available providers: {available_providers}"
                )
            engine_options = {
                "det_use_dml": True,
                "cls_use_dml": True,
                "rec_use_dml": True,
            }
            inference_provider = "DmlExecutionProvider"
        engine = RapidOCR(**engine_options)
        print(f"OCR PROVIDER {inference_provider}", flush=True)
        failures = 0
        for index, (item, source_issue) in enumerate(queue, start=1):
            digest = str(item["sha256"])
            kind = str(item["kind"])
            urls = [str(value) for value in item["urls"]]
            body = (state_dir / str(item["body_path"])).read_bytes()
            document_dir = ocr_dir / digest
            document_dir.mkdir(parents=True, exist_ok=True)
            print(
                f"OCR ASSET {index}/{len(queue)} kind={kind} sha256={digest} url={urls[0]}",
                flush=True,
            )
            started = time.perf_counter()
            entry: dict[str, object] = {
                "sha256": digest,
                "kind": kind,
                "url": urls[0],
                "duplicate_urls": urls[1:],
                "body_path": str(item["body_path"]),
                "source_issue": source_issue,
                "inference_provider": inference_provider,
                "generated_at": now_beijing(),
            }
            if hashlib.sha256(body).hexdigest() != digest:
                failures += 1
                entry.update(
                    {
                        "status": "failed",
                        "pages": None,
                        "text_characters": 0,
                        "seconds": 0,
                        "error": "cached response SHA-256 does not match its manifest digest",
                    }
                )
                manifest[digest] = entry
                print(
                    f"OCR FAILED sha256={digest} error={entry['error']}",
                    flush=True,
                )
                if index % args.checkpoint_every == 0:
                    save_manifest(manifest_path, manifest)
                continue
            had_checkpoint_evidence = not args.force and any(
                document_dir.glob("*.json")
            )
            try:
                if kind == "pdf":
                    pages, combined, resumed_units, decode_warnings = ocr_document(
                        engine,
                        body,
                        document_dir,
                        args.scale,
                        args.min_confidence,
                        args.tile_height,
                        args.tile_overlap,
                        args.force,
                    )
                else:
                    pages, combined, resumed_units, decode_warnings = ocr_image_asset(
                        engine,
                        body,
                        document_dir,
                        args.min_confidence,
                        args.tile_height,
                        args.tile_overlap,
                        args.max_image_side,
                        args.force,
                    )
                if resumed_units == pages:
                    entry["inference_provider"] = "checkpoint"
                elif resumed_units:
                    entry["inference_provider"] = (
                        f"checkpoint+{inference_provider}"
                    )
                if decode_warnings:
                    entry["decode_warnings"] = decode_warnings
                normalized = normalize_ocr_text(combined) if combined.strip() else ""
                visible_characters = sum(
                    not character.isspace() for character in normalized
                )
                minimum_characters = (
                    args.min_pdf_text_characters
                    if kind == "pdf"
                    else args.min_image_text_characters
                )
                (document_dir / "combined.txt").write_text(
                    combined + "\n", encoding="utf-8"
                )
                (document_dir / "combined.normalized.txt").write_text(
                    normalized, encoding="utf-8"
                )
                entry.update(
                    {
                        "status": (
                            "success"
                            if visible_characters >= minimum_characters
                            else "no_text"
                        ),
                        "pages": pages,
                        "text_characters": visible_characters,
                        "seconds": round(time.perf_counter() - started, 3),
                        "error": None,
                    }
                )
                if entry["status"] == "no_text":
                    print(
                        f"OCR NO_TEXT sha256={digest} characters={visible_characters}",
                        flush=True,
                    )
            except Exception as error:
                failures += 1
                if had_checkpoint_evidence:
                    entry["inference_provider"] = (
                        f"checkpoint+{inference_provider}"
                    )
                entry.update(
                    {
                        "status": "failed",
                        "pages": None,
                        "text_characters": 0,
                        "seconds": round(time.perf_counter() - started, 3),
                        "error": f"{type(error).__name__}: {error}",
                    }
                )
                print(f"OCR FAILED sha256={digest} error={entry['error']}", flush=True)
            manifest[digest] = entry
            if index % args.checkpoint_every == 0:
                save_manifest(manifest_path, manifest)

        save_manifest(manifest_path, manifest)

        print(
            f"OCR COMPLETE processed={len(queue)} failures={failures} ",
            f"manifest={manifest_path}",
            flush=True,
        )
        return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
