#!/usr/bin/env python3
"""
Regenerates app/src/main/assets/root_data.json from a local clone of
https://github.com/awesome-android-root/awesome-android-root (MIT License).

Usage:
    git clone --depth 1 https://github.com/awesome-android-root/awesome-android-root.git
    python3 tools/update_data.py awesome-android-root

The device data (brand support and temporary-root targets) is parsed from the
rooting guides in the same repository.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_URL = "https://github.com/awesome-android-root/awesome-android-root"
BLOB = REPO_URL + "/blob/main/"
KNOWN_TAGS = {"FOSS", "Proprietary", "[M]", "[K]", "[A]", "[LSP]"}

ENTRY = re.compile(r"^\s*[-*]\s+\*\*\[(?P<name>[^\]]+)\]\((?P<url>[^)]+)\)\*\*\s*[-–—:]?\s*(?P<rest>.*)$")
TAG = re.compile(r"`([^`]+)`")


def clean_md(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)       # links -> text
    text = re.sub(r"<[^>]+>", "", text)                        # html
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?<!\w)\*(?!\s)([^*]+)\*(?!\w)", r"\1", text)
    text = text.replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def front_title(md: str, fallback: str) -> str:
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', md, re.M)
    return m.group(1) if m else fallback


def parse_apps(repo: Path):
    folder = repo / "docs" / "apps-and-modules"
    categories, apps, seen = [], [], set()
    for f in sorted(folder.glob("*.md")):
        if f.name == "index.md":
            continue
        md = f.read_text(encoding="utf-8")
        cat_id = f.stem
        h1 = re.search(r"^#\s+(.+)$", md, re.M)
        cat_name = clean_md(h1.group(1)) if h1 else front_title(md, cat_id)
        count = 0
        section = ""
        for line in md.splitlines():
            if line.startswith("## "):
                section = clean_md(line[3:])
                continue
            if line.startswith("### "):
                section = clean_md(line[4:])
                continue
            m = ENTRY.match(line)
            if not m:
                continue
            url = m.group("url").strip()
            if not url.startswith("http"):
                continue
            raw_name = m.group("name")
            featured = "⭐" in raw_name
            name = clean_md(raw_name.replace("⭐", ""))
            rest = m.group("rest")
            tags = [t for t in TAG.findall(rest) if t in KNOWN_TAGS]
            desc = rest
            # drop trailing badge block
            desc = re.sub(r"(\s*`(FOSS|Proprietary|\[M\]|\[K\]|\[A\]|\[LSP\])`)+\s*$", "", desc)
            desc = clean_md(desc)
            desc = re.sub(r"(\s*(\bFOSS\b|\bProprietary\b|\||🌱|▶️|▶|\ufe0f|\[(M|K|A|LSP)\]))+\s*$", "", desc).strip()
            key = (cat_id, name.lower(), url)
            if key in seen:
                continue
            seen.add(key)
            host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
            apps.append({
                "name": name,
                "url": url,
                "github": host == "github.com",
                "description": desc,
                "category": cat_id,
                "section": section,
                "featured": featured,
                "foss": "FOSS" in tags,
                "fdroid": "🌱" in rest,
                "play": "▶" in rest,
                "frameworks": [t.strip("[]") for t in tags if t.startswith("[")],
            })
            count += 1
        short = re.sub(r"^Best\s+", "", cat_name)
        short = re.sub(r"\s+(for|on)\s+(Rooted\s+)?(Android|Root)$", "", short)
        short = re.sub(r"\s+for Root$", "", short)
        categories.append({
            "id": cat_id,
            "name": cat_name,
            "short": short,
            "count": count,
            "source": BLOB + "docs/apps-and-modules/" + f.name,
        })
    categories.sort(key=lambda c: (c["id"] != "root-management", c["name"]))
    return categories, apps


def table_rows(md: str, header_startswith: str):
    lines = md.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("| " + header_startswith) or line.startswith("|" + header_startswith):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                rows.append(cells)
            return rows
    return []


GUIDES = {
    "Google Pixel": "how-to-root-pixel-phone.md",
    "Samsung Galaxy": "how-to-root-samsung-phone.md",
    "Xiaomi / Redmi / POCO": "how-to-root-xiaomi-phone.md",
    "OnePlus": "how-to-root-oneplus-phone.md",
    "Nothing": "how-to-root-nothing-phone.md",
    "Motorola": "how-to-root-motorola-phone.md",
}

STATUS = {  # simple traffic-light rating used by the app's badges
    "Google Pixel": "easy", "OnePlus": "easy", "Nothing": "easy",
    "Motorola": "moderate", "Sony Xperia": "moderate", "ASUS": "moderate",
    "Xiaomi / Redmi / POCO": "restricted", "Samsung Galaxy": "restricted",
    "OPPO / Realme / vivo / Honor": "restricted", "Huawei": "unavailable",
}


def parse_devices(repo: Path):
    guides = repo / "docs" / "rooting-guides"
    unlock = (guides / "how-to-unlock-bootloader.md").read_text(encoding="utf-8")
    compare = (guides / "root-framework-comparison.md").read_text(encoding="utf-8")

    policy = {}
    for cells in table_rows(unlock, "Manufacturer"):
        if len(cells) >= 4:
            policy[clean_md(cells[0])] = {
                "method": clean_md(cells[1]),
                "wait": clean_md(cells[2]),
                "limitation": clean_md(cells[3]),
            }
    guidance = {}
    for cells in table_rows(compare, "Device family"):
        if len(cells) >= 2:
            guidance[clean_md(cells[0])] = clean_md(cells[1])

    def pol(*names):
        for n in names:
            if n in policy:
                return policy[n]
        return {}

    brands = []
    order = [
        ("Google Pixel", pol("Google Pixel"), guidance.get("Google Pixel", "")),
        ("OnePlus", pol("OnePlus"), guidance.get("OnePlus", "")),
        ("Nothing", pol("Nothing"), guidance.get("Nothing", "")),
        ("Motorola", pol("Motorola"), guidance.get("Motorola / ASUS", "")),
        ("Sony Xperia", {"method": "Unlock code from Sony Developer Portal",
                         "wait": "Usually none",
                         "limitation": "Check eligibility with your IMEI; unlocking erases DRM keys (camera quality can drop)."},
         "Eligibility depends on model and IMEI. DRM key loss is permanent."),
        ("ASUS", {"method": "Official ASUS unlock tool (model-dependent)", "wait": "Varies",
                  "limitation": "Tool availability varies by model and region."},
         guidance.get("Motorola / ASUS", "")),
        ("Xiaomi / Redmi / POCO", pol("Xiaomi/Redmi/POCO"), guidance.get("Xiaomi / Redmi / POCO", "")),
        ("Samsung Galaxy", pol("Samsung"), guidance.get("Samsung Galaxy", "")),
        ("OPPO / Realme / vivo / Honor", {"method": "Deep Testing app (OPPO/Realme), model-dependent",
                                          "wait": "Often ~7 days",
                                          "limitation": "Many models have no official unlock at all."},
         guidance.get("OPPO / Realme / vivo / Honor", "")),
        ("Huawei", pol("Huawei"), "Official unlock codes are no longer offered for current devices."),
    ]
    for name, p, g in order:
        guide = GUIDES.get(name)
        brands.append({
            "brand": name,
            "status": STATUS.get(name, "moderate"),
            "method": p.get("method", ""),
            "wait": p.get("wait", ""),
            "limitation": p.get("limitation", ""),
            "guidance": g,
            "guide": BLOB + "docs/rooting-guides/" + (guide or "how-to-unlock-bootloader.md"),
        })

    temp_md = (guides / "root-without-unlocking-bootloader.md").read_text(encoding="utf-8")
    temp = []
    for cells in table_rows(temp_md, "Project / repository"):
        if len(cells) < 4:
            continue
        link = re.search(r"\[([^\]]+)\]\(([^)]+)\)", cells[0])
        if not link:
            continue
        temp.append({
            "project": clean_md(link.group(1)),
            "url": link.group(2),
            "devices": clean_md(cells[1]),
            "firmware": clean_md(cells[2]),
            "notes": clean_md(re.sub(r"\[Documentation\]\([^)]*\)\.?", "", cells[3])),
        })

    frameworks = []
    for cells in table_rows(compare, "If you want..."):
        if len(cells) >= 3:
            frameworks.append({"want": clean_md(cells[0]), "choose": clean_md(cells[1]), "why": clean_md(cells[2])})
    return brands, temp, frameworks


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    repo = Path(sys.argv[1])
    categories, apps = parse_apps(repo)
    brands, temp, frameworks = parse_devices(repo)
    out = {
        "source": REPO_URL,
        "license": "MIT - Awesome Android Root contributors",
        "generated": date.today().isoformat(),
        "categories": categories,
        "apps": apps,
        "brands": brands,
        "tempRoot": temp,
        "frameworkPicks": frameworks,
    }
    target = Path(__file__).resolve().parent.parent / "app/src/main/assets/root_data.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(apps)} apps in {len(categories)} categories, {len(brands)} brands, "
          f"{len(temp)} temp-root targets -> {target}")


if __name__ == "__main__":
    main()
