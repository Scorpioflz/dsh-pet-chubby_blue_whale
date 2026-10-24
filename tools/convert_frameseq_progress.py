# -*- coding: utf-8 -*-
"""帧序列转换器（带进度显示和 ETA）——包装 convert_frameseq.py 的逻辑。

用法同 convert_frameseq.py：
    python tools/convert_frameseq_progress.py --character shenshen --include random,events
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pet.frameseq_provision import (  # noqa: E402
    HOT_FOLDERS,
    clip_out_dir,
    convert_clip,
    hot_webms,
    is_lossy_clip,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="帧序列转换器（带进度）")
    parser.add_argument("--character", default="shenshen")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--include", default="")
    args = parser.parse_args()

    videos = REPO_ROOT / "assets" / "characters" / args.character / "videos"
    if not videos.is_dir():
        print(f"角色素材目录不存在: {videos}", file=sys.stderr)
        return 1

    folders = set(HOT_FOLDERS)
    folders.update(f for f in args.include.split(",") if f)

    webms = hot_webms(videos, folders)
    if not webms:
        print("没有匹配目录的 webm", file=sys.stderr)
        return 1

    total = len(webms)
    out_root = videos.parent / "frameseq"
    done = skipped = failed = 0
    start = time.monotonic()

    for i, webm in enumerate(webms, 1):
        rel = webm.relative_to(videos).with_suffix("")
        out_dir = clip_out_dir(webm, videos, out_root)

        elapsed = time.monotonic() - start
        eta = elapsed / max(1, i - 1) * (total - i) if i > 1 else 0
        pct = i * 100 // total
        print(f"\r[{i}/{total}] {pct}% | {rel} | {elapsed:.0f}s elapsed | ~{eta:.0f}s remaining   ", end="", flush=True)

        converted, err = convert_clip(
            webm, out_dir, force=args.force,
            lossy=is_lossy_clip(webm, videos),
        )
        if err:
            failed += 1
            print(f"\nFAIL {rel}: {err}", file=sys.stderr)
            continue
        if converted:
            done += 1
        else:
            skipped += 1

    elapsed = time.monotonic() - start
    print(f"\nDone: {done} converted / {skipped} skipped / {failed} failed | {elapsed:.0f}s total")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())