"""
将 heroes.json 中的 cdn.tlidb.com 头像与特性图标下载到 torchlight-builder/public/assets/heroes/，
并把 JSON 中的 URL 改写为 /assets/heroes/... 本地路径。

重新爬取后若 JSON 又变回 CDN，可再次运行本脚本。
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND = ROOT_DIR / "torchlight-builder"
HEROES_JSON = FRONTEND / "src" / "data" / "heroes" / "heroes.json"
PUBLIC_HEROES = FRONTEND / "public" / "assets" / "heroes"
CDN_PREFIX = "https://cdn.tlidb.com"


def cdn_url_to_local(url: str) -> tuple[Path, str] | tuple[None, None]:
    if not url or not isinstance(url, str):
        return None, None
    if url.startswith("/assets/heroes/"):
        return None, None
    if not url.startswith(CDN_PREFIX):
        return None, None
    path = url[len(CDN_PREFIX) :].lstrip("/")
    if "/Icon/Portrait/" in path:
        i = path.index("/Icon/Portrait/") + len("/Icon/Portrait/")
        rest = path[i:]
        disk = PUBLIC_HEROES / "portraits" / Path(rest)
        web = "/assets/heroes/portraits/" + rest.replace("\\", "/")
        return disk, web
    if "/HeroTraits/" in path:
        i = path.index("/HeroTraits/") + len("/HeroTraits/")
        rest = path[i:]
        disk = PUBLIC_HEROES / "traits" / Path(rest)
        web = "/assets/heroes/traits/" + rest.replace("\\", "/")
        return disk, web
    return None, None


def local_url_to_cdn_and_disk(web: str) -> tuple[str, Path] | tuple[None, None]:
    """本地 /assets/heroes/... -> (cdn_url, 磁盘路径)，用于补全已本地化 JSON 的下载。"""
    if not web or not isinstance(web, str):
        return None, None
    if not web.startswith("/assets/heroes/"):
        return None, None
    tail = web[len("/assets/heroes/") :].lstrip("/")
    if tail.startswith("portraits/"):
        rest = tail[len("portraits/") :]
        cdn = f"{CDN_PREFIX}/UI/Textures/Common/Icon/Portrait/{rest}"
        disk = PUBLIC_HEROES / "portraits" / Path(rest)
        return cdn, disk
    if tail.startswith("traits/"):
        rest = tail[len("traits/") :]
        cdn = f"{CDN_PREFIX}/UI/Textures/Common/Icon/Skill/HeroTraits/{rest}"
        disk = PUBLIC_HEROES / "traits" / Path(rest)
        return cdn, disk
    return None, None


def resolve_download_task(url: str) -> tuple[str, Path] | tuple[None, None]:
    """返回 (cdn_url, 目标文件路径)。"""
    if not url or not isinstance(url, str):
        return None, None
    if url.startswith(CDN_PREFIX):
        disk, _ = cdn_url_to_local(url)
        return (url, disk) if disk else (None, None)
    cdn, disk = local_url_to_cdn_and_disk(url)
    return (cdn, disk) if cdn and disk else (None, None)


def collect_urls(heroes: list) -> set[str]:
    out: set[str] = set()
    for h in heroes:
        p = h.get("portrait")
        if p:
            out.add(p)
        for t in h.get("traits") or []:
            ic = t.get("icon")
            if ic:
                out.add(ic)
    return out


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


def apply_local_paths_to_heroes(heroes: list) -> None:
    """将 CDN URL 改写为 /assets/heroes/...（不下载）。"""
    for h in heroes:
        _, web = cdn_url_to_local(h.get("portrait") or "")
        if web:
            h["portrait"] = web
        for t in h.get("traits") or []:
            _, w = cdn_url_to_local(t.get("icon") or "")
            if w:
                t["icon"] = w


def main() -> None:
    if not HEROES_JSON.is_file():
        print(f"Missing {HEROES_JSON}", file=sys.stderr)
        sys.exit(1)

    heroes = json.loads(HEROES_JSON.read_text(encoding="utf-8"))
    urls = sorted(collect_urls(heroes))
    tasks: list[tuple[str, Path]] = []
    seen_disk: set[str] = set()
    for u in urls:
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
    for u, disk in tasks:
        if download_one(u, disk):
            ok += 1
        else:
            failed.append(u)

    apply_local_paths_to_heroes(heroes)
    HEROES_JSON.write_text(
        json.dumps(heroes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Downloaded/verified {ok}/{len(tasks)} files under {PUBLIC_HEROES}")
    print(f"Updated {HEROES_JSON}")
    if failed:
        print(f"{len(failed)} download(s) failed; re-run this script to retry.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
