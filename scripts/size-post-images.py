#!/usr/bin/env python3
# ABOUTME: Adds width, height and loading="lazy" to local <img> tags in post markdown files.
# ABOUTME: Sizes come from the image files on disk. Dry run unless --write is given.
import argparse
import os
import re
import subprocess
import sys

IMG_TAG = re.compile(r"<img\b([^>]*?)(/?)>")
SRC = re.compile(r'\ssrc="([^"]*)"')
SIZE_ATTRS = re.compile(r'\s+(?:width|height|loading)="[^"]*"')


def image_size(path):
    out = subprocess.check_output(
        ["magick", "identify", "-format", "%w %h", path + "[0]"], text=True
    )
    width, height = out.split()
    return width, height


def rewrite(md_path, text):
    changes = []
    skipped = []

    def replace(match):
        attrs, close = match.group(1), match.group(2)
        src = SRC.search(attrs)
        if not src:
            return match.group(0)
        url = src.group(1)
        if re.match(r"https?://", url):
            skipped.append(url)
            return match.group(0)
        path = os.path.normpath(os.path.join(os.path.dirname(md_path), url))
        if not os.path.isfile(path):
            skipped.append(url + " (file not found)")
            return match.group(0)
        width, height = image_size(path)
        rest = SIZE_ATTRS.sub("", attrs)
        rest = SRC.sub(
            lambda m: (
                ' src="%s" width="%s" height="%s" loading="lazy"'
                % (m.group(1), width, height)
            ),
            rest,
            count=1,
        )
        new = "<img%s%s>" % (rest, close)
        if new != match.group(0):
            changes.append((match.group(0), new))
        return new

    return IMG_TAG.sub(replace, text), changes, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="post markdown files")
    parser.add_argument("--write", action="store_true", help="edit the files")
    args = parser.parse_args()

    total = 0
    for md_path in args.files:
        with open(md_path) as f:
            text = f.read()
        new_text, changes, skipped = rewrite(md_path, text)
        for url in skipped:
            print("%s: skipped %s" % (md_path, url), file=sys.stderr)
        if not changes:
            continue
        total += len(changes)
        print("%s: %d tag(s)" % (md_path, len(changes)))
        if args.write:
            with open(md_path, "w") as f:
                f.write(new_text)
        else:
            for old, new in changes[:2]:
                print("  - " + old)
                print("  + " + new)
    print("%s %d tag(s)" % ("updated" if args.write else "would update", total))


if __name__ == "__main__":
    main()
