"""
将 src/data/talents/*.json 中的 cdn.tlidb.com 图标 URL 下载到
torchlight-builder/public/assets/talents/（路径与 CDN 上 UI/ 之后保持一致），
并把 JSON 中的链接改写为 /assets/talents/... 。

用法：在仓库根目录执行  python sync_talent_assets.py
重新生成天赋 JSON 后若又回到 CDN，可再运行本脚本；build_all_talent_trees.py 也会在写入前尽量改写为本地路径。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND = ROOT_DIR / "torchlight-builder"
TALENTS_DATA_DIR = FRONTEND / "src" / "data" / "talents"
PUBLIC_TALENTS = FRONTEND / "public" / "assets" / "talents"
CDN_PREFIX = "https://cdn.tlidb.com"


def cdn_url_to_local(url: str) -> tuple[Path, str] | tuple[None, None]:
    if not url or not isinstance(url, str):
        return None, None
    if url.startswith("/assets/talents/"):
        return None, None
    if not url.startswith(CDN_PREFIX):
        return None, None
    rest = url[len(CDN_PREFIX) :].lstrip("/")
    disk = PUBLIC_TALENTS / Path(rest)
    web = "/assets/talents/" + rest.replace("\\", "/")
    return disk, web


def local_url_to_cdn_and_disk(web: str) -> tuple[str, Path] | tuple[None, None]:
    if not web or not isinstance(web, str):
        return None, None
    if not web.startswith("/assets/talents/"):
        return None, None
    rest = web[len("/assets/talents/") :].lstrip("/")
    cdn = f"{CDN_PREFIX}/{rest}"
    disk = PUBLIC_TALENTS / Path(rest)
    return cdn, disk


def resolve_download_task(url: str) -> tuple[str, Path] | tuple[None, None]:
    if not url or not isinstance(url, str):
        return None, None
    if url.startswith(CDN_PREFIX):
        disk, _ = cdn_url_to_local(url)
        return (url, disk) if disk else (None, None)
    cdn, disk = local_url_to_cdn_and_disk(url)
    return (cdn, disk) if cdn and disk else (None, None)


def collect_asset_urls(obj, out: set[str]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            collect_asset_urls(v, out)
    elif isinstance(obj, list):
        for item in obj:
            collect_asset_urls(item, out)
    elif isinstance(obj, str):
        if obj.startswith(CDN_PREFIX) or obj.startswith("/assets/talents/"):
            out.add(obj)


def apply_local_paths_to_talent_tree(obj) -> None:
    """递归将 CDN 图标 URL 改为 /assets/talents/...（不下载）。"""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str):
                _, web = cdn_url_to_local(v)
                if web:
                    obj[k] = web
            else:
                apply_local_paths_to_talent_tree(v)
    elif isinstance(obj, list):
        for item in obj:
            apply_local_paths_to_talent_tree(item)


def download_one(url: str, dest: Path, *, timeout_sec: float = 90.0, attempts: int = 4) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return True
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://tlidb.com/",
        },
    )
    last_err: BaseException | None = None
    for n in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                data = resp.read()
            if not data:
                last_err = RuntimeError("empty body")
            else:
                dest.write_bytes(data)
                return True
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            last_err = e
        if n + 1 < attempts:
            time.sleep(1.5 * (n + 1))
    print(f"FAIL {url} -> {dest}: {last_err}", file=sys.stderr)
    return False


def iter_talent_json_files() -> list[Path]:
    if not TALENTS_DATA_DIR.is_dir():
        return []
    return sorted(TALENTS_DATA_DIR.glob("*.json"))


def main() -> None:
    files = iter_talent_json_files()
    if not files:
        print(f"No JSON under {TALENTS_DATA_DIR}", file=sys.stderr)
        sys.exit(1)

    all_urls: set[str] = set()
    loaded: list[tuple[Path, object]] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        loaded.append((path, data))
        collect_asset_urls(data, all_urls)

    tasks: list[tuple[str, Path]] = []
    seen_disk: set[str] = set()
    for u in sorted(all_urls):
        cdn_u, disk = resolve_download_task(u)
        if disk is None or cdn_u is None:
            continue
        key = str(disk.resolve())
        if key in seen_disk:
            continue
        seen_disk.add(key)
        tasks.append((cdn_u, disk))

    ok = 0
    failed: list[str] = []
    for cdn_u, disk in tasks:
        if download_one(cdn_u, disk):
            ok += 1
        else:
            failed.append(cdn_u)

    for path, data in loaded:
        apply_local_paths_to_talent_tree(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Downloaded/verified {ok}/{len(tasks)} files under {PUBLIC_TALENTS}")
    print(f"Updated {len(loaded)} JSON file(s) in {TALENTS_DATA_DIR}")
    if failed:
        print(f"{len(failed)} download(s) failed; re-run to retry.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
