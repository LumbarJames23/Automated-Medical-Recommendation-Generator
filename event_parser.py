import os
import re
from collections import defaultdict

from app_config import EXERCISES_DIR, SUPPLEMENTS_DIR, HYPERLINKS_DIR, RECOMMENDATION_RULES
from utils import remove_html_tags, find_file_case_insensitive, sort_regions, sanitize_filename


def _extract_name(title: str) -> str:
    name_match = re.match(r"[+]?([A-Za-z']+,\s+[A-Za-z']+)", title)
    if name_match:
        return name_match.group(1).strip()
    return sanitize_filename(title.strip()) if title.strip() else "MISSING_EVENT_TITLE"


def _extract_surg(full: str) -> str | None:
    surg_match = re.search(r"\{([^}]+)\}", full)
    return surg_match.group(1).strip() if surg_match else None


def _extract_dob(full: str) -> str:
    dob_match = re.search(r"DOB[:\s]*(\d{2}/\d{2}/\d{4})", full)
    return dob_match.group(1) if dob_match else "MISSING"


def _classify_entry(kind: str, regions: list, img: dict, pt: list) -> None:
    if kind in ["CT", "MRI", "DXR"]:
        for region in regions:
            if region not in img[kind]:
                img[kind].append(region)
    elif kind == "PT":
        for region in regions:
            if region not in pt:
                pt.append(region)


def _parse_bracket_blocks(blocks: list[str]) -> tuple[dict, list]:
    img, pt = defaultdict(list), []
    for block in blocks:
        for entry in [e.strip().lower() for e in block.split(",")]:
            if not entry:
                continue
            words = entry.split()
            _classify_entry(words[0].upper(), [w.upper() for w in words[1:]], img, pt)
    for k in img:
        img[k] = sort_regions(img[k])
    return img, sort_regions(pt)


def _parse_recommendations(blocks: list[str]) -> list:
    recs = []
    for item in blocks:
        for token in [i.strip() for i in item.split(",")]:
            if re.match(r"^(PT|CT|MRI|DXR)\s", token.upper()):
                continue
            if token and token not in recs:
                recs.append(token)
    return recs


def _resolve_attachments(recs: list) -> tuple[list, list]:
    attachments, attachment_log = [], []
    for rec in recs:
        rec_upper = rec.upper()
        rule = RECOMMENDATION_RULES.get(rec_upper)
        if rule and rule.get("type") == "exercise_bundle":
            for filename in rule.get("exercise_files", []):
                path = os.path.join(EXERCISES_DIR, filename)
                if os.path.exists(path):
                    attachments.append(path)
                    attachment_log.append(f"  FOUND {path}")
                else:
                    attachment_log.append(f"  MISSING - {filename} PDF/LINK")
            continue
        pdf_target = rule.get("pdf_name") if rule else None
        pdf_path = find_file_case_insensitive(SUPPLEMENTS_DIR, pdf_target or rec)
        link_path = find_file_case_insensitive(HYPERLINKS_DIR, rec)
        if pdf_path:
            attachments.append(pdf_path)
            attachment_log.append(f"  FOUND {pdf_path}")
        elif link_path:
            attachment_log.append(f"  FOUND {link_path}")
        else:
            attachment_log.append(f"  MISSING - {rec} PDF/LINK")
    return attachments, attachment_log


def _log_parsed(name, dob, surg, img, pt, recs, attachment_log):
    print(f"NAME: {name}")
    print(f"DOB: {dob}")
    print(f"SURGICAL RECOMMENDATION: {surg if surg else 'NONE'}")
    print(f"IMG: {dict(img) if img else 'NONE'}")
    print(f"PT: {pt if pt else 'NONE'}")
    print(f"RECOMMENDATIONS: {recs if recs else 'NONE'}")
    print("ATTACHMENTS:")
    print("\n".join(attachment_log) if attachment_log else "  NONE")


def parse_event_data(event: dict) -> dict | None:
    title = event.get("summary", "")
    desc = event.get("description", "")
    print(f"\n{'-'*60}\nProcessing: {title}")

    if not desc or "RECS:" not in desc:
        print(f"{title} - Skipped (no RECS: found)")
        return None

    full = remove_html_tags(desc)
    bracket_blocks = re.findall(r"\[([^\]]+)\]", full)
    name = _extract_name(title)
    surg = _extract_surg(full)
    dob = _extract_dob(full)
    img, pt = _parse_bracket_blocks(bracket_blocks)
    recs = _parse_recommendations(bracket_blocks)
    attachments, attachment_log = _resolve_attachments(recs)

    _log_parsed(name, dob, surg, img, pt, recs, attachment_log)

    return {
        "name": name,
        "dob": dob,
        "pt": pt,
        "img": img,
        "surg": surg,
        "recommendations": recs,
        "attachments": attachments,
        "title": title,
    }
