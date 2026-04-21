import os
import re
from collections import defaultdict

from app_config import EXERCISES_DIR, SUPPLEMENTS_DIR, HYPERLINKS_DIR, RECOMMENDATION_RULES
from utils import remove_html_tags, find_file_case_insensitive, sort_regions, sanitize_filename


def parse_event_data(event):
    title = event.get("summary", "")
    desc = event.get("description", "")
    print(f"\n{'-'*60}\nProcessing: {title}")

    if not desc or "RECS:" not in desc:
        print(f"{title} - Skipped (no RECS: found)")
        return None

    full = remove_html_tags(desc)

    name_match = re.match(r"[+]?([A-Za-z']+,\s+[A-Za-z']+)", title)
    if name_match:
        name = name_match.group(1).strip()
    else:
        name = sanitize_filename(title.strip()) if title.strip() else "MISSING_EVENT_TITLE"

    surg_match = re.search(r"\{([^}]+)\}", full)
    surg = surg_match.group(1).strip() if surg_match else None

    dob_match = re.search(r"DOB[:\s]*(\d{2}/\d{2}/\d{4})", full)
    dob = dob_match.group(1) if dob_match else "MISSING"

    img, pt = defaultdict(list), []
    bracket_blocks = re.findall(r"\[([^\]]+)\]", full)

    for block in bracket_blocks:
        entries = [e.strip().lower() for e in block.split(",")]
        for entry in entries:
            if not entry:
                continue

            words = entry.split()
            if not words:
                continue

            kind = words[0].upper()
            regions = [w.upper() for w in words[1:]]

            if kind in ["CT", "MRI", "DXR"]:
                for region in regions:
                    if region not in img[kind]:
                        img[kind].append(region)
            elif kind == "PT":
                for region in regions:
                    if region not in pt:
                        pt.append(region)

    for k in img:
        img[k] = sort_regions(img[k])
    pt = sort_regions(pt)

    bracket_items = re.findall(r"\[([^\]]+)\]", full)
    recs = []

    for item in bracket_items:
        tokens = [i.strip() for i in item.split(",")]
        for token in tokens:
            if re.match(r"^(PT|CT|MRI|DXR)\s", token.strip().upper()):
                continue
            if token and token not in recs:
                recs.append(token)

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

        pdf_target = None
        if rule:
            pdf_target = rule.get("pdf_name")

        pdf_path = find_file_case_insensitive(SUPPLEMENTS_DIR, pdf_target or rec)
        link_path = find_file_case_insensitive(HYPERLINKS_DIR, rec)

        if pdf_path and os.path.exists(pdf_path):
            attachments.append(pdf_path)
            attachment_log.append(f"  FOUND {pdf_path}")
        elif link_path and os.path.exists(link_path):
            attachment_log.append(f"  FOUND {link_path}")
        else:
            attachment_log.append(f"  MISSING - {rec} PDF/LINK")

    print(f"NAME: {name}")
    print(f"DOB: {dob}")
    print(f"SURGICAL RECOMMENDATION: {surg if surg else 'NONE'}")
    print(f"IMG: {dict(img) if img else 'NONE'}")
    print(f"PT: {pt if pt else 'NONE'}")
    print(f"RECOMMENDATIONS: {recs if recs else 'NONE'}")
    print("ATTACHMENTS:")
    print("\n".join(attachment_log) if attachment_log else "  NONE")

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