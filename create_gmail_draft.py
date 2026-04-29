import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from app_config import (
    CLINIC_NAME,
    PHONE,
    WELCOME_EMAIL,
    OFFICE_EMAIL,
    COORDINATOR_EMAIL,
    HYPERLINKS_DIR,
    SUPPLEMENTS_DIR,
    RECOMMENDATION_RULES,
    IMAGING_DISPLAY_NAMES,
    NON_SURGICAL_TEMPLATE,
    SURGICAL_TEMPLATE,
    SUBJECT_PREFIX,
    PT_SCHEDULE,
    PT_IMAGING_NOTE,
    SURGICAL_IMAGING_PREAMBLE,
    SURGICAL_RECS_PREAMBLE,
    CLOSING_MESSAGE,
)
from utils import find_file_case_insensitive, load_text_file, title_case_words, region_verbose


def find_link_text(name: str) -> str | None:
    path = find_file_case_insensitive(HYPERLINKS_DIR, name)
    return load_text_file(path) if path else None


def load_template(path: str) -> str:
    text = load_text_file(path)
    if text is None:
        raise FileNotFoundError(f"Missing email template: {path}")
    return text


def render_placeholders(template: str, replacements: dict[str, str]) -> str:
    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def recommendation_display_text(rec: str) -> str:
    rule = RECOMMENDATION_RULES.get(rec.upper())
    if rule and "display" in rule:
        return rule["display"]
    return title_case_words(rec)


def _build_imaging_items(img: dict) -> str:
    return "".join(
        f"<li>{IMAGING_DISPLAY_NAMES.get(img_type.upper(), img_type)} of the {', '.join(region_verbose(r) for r in regs)}</li>"
        for img_type, regs in img.items()
    )


def _build_rec_bullet(rec: str) -> str:
    text = recommendation_display_text(rec)
    pdf_target = RECOMMENDATION_RULES.get(rec.upper(), {}).get("pdf_name", rec)
    pdf_exists = find_file_case_insensitive(SUPPLEMENTS_DIR, pdf_target)
    link = find_link_text(rec) if not pdf_exists else None
    if link:
        return f'<li><a href="{link}">{text}</a></li>'
    return f"<li>{text}</li>"


def _build_recs_bullets(recs: list) -> str:
    return "".join(_build_rec_bullet(rec) for rec in recs)


def _build_non_surgical_body(parsed: dict, date_line: str) -> str:
    header = load_template(NON_SURGICAL_TEMPLATE)
    body = render_placeholders(header, {
        "{$NAME}": parsed["name"],
        "{$DATE}": date_line,
        "{$CLINIC_NAME}": CLINIC_NAME,
        "{$PHONE}": PHONE,
    })

    pt = set(parsed["pt"])
    if pt:
        pt_regions = (
            "Cervical Spine and Lumbar Spine"
            if pt == {"CS", "LS"}
            else " and ".join(region_verbose(r) for r in pt)
        )
        body += f"<li>Physical Therapy of the {pt_regions} {PT_SCHEDULE}.</li>"

    if parsed["img"]:
        imaging_note = f" <b><i>{PT_IMAGING_NOTE}</i></b>" if pt else ""
        body += f"<li>New Imaging:{imaging_note}<ul>{_build_imaging_items(parsed['img'])}</ul></li>"

    body += _build_recs_bullets(parsed["recommendations"])
    body += f"</ul><br>{CLOSING_MESSAGE}<br>--"
    return body


def _build_surgical_body(parsed: dict, date_line: str) -> str:
    header = load_template(SURGICAL_TEMPLATE)
    body = render_placeholders(header, {
        "{$NAME}": parsed["name"],
        "{$DATE}": date_line,
        "{$CLINIC_NAME}": CLINIC_NAME,
        "{$SURG}": parsed["surg"],
        "{$COORDINATOR_EMAIL}": COORDINATOR_EMAIL,
    })

    if parsed["img"]:
        body += f"{SURGICAL_IMAGING_PREAMBLE}<br><ul>{_build_imaging_items(parsed['img'])}</ul>"

    recs = parsed["recommendations"]
    if recs:
        body += f"{SURGICAL_RECS_PREAMBLE}<br><ul>{_build_recs_bullets(recs)}</ul><br>"

    body += f"{CLOSING_MESSAGE}<br>--"
    return body


def _attach_pdfs(msg: MIMEMultipart, attachments: list) -> None:
    for f in attachments:
        try:
            filename = os.path.basename(f)
            with open(f, "rb") as fi:
                part = MIMEApplication(fi.read(), Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)
        except Exception:
            print(f"Error attaching file: {f}")


def create_gmail_draft(gmail_service, parsed: dict, event_date) -> None:
    name = parsed["name"]
    date_line = event_date.strftime("%A, %B %d, %Y")
    subject = f"{SUBJECT_PREFIX} - {name}"

    body = _build_surgical_body(parsed, date_line) if parsed["surg"] else _build_non_surgical_body(parsed, date_line)

    msg = MIMEMultipart()
    msg.attach(MIMEText(body, "html"))
    msg["to"] = ""
    msg["cc"] = (
        f"{WELCOME_EMAIL}, {OFFICE_EMAIL}, {COORDINATOR_EMAIL}"
        if parsed["surg"]
        else f"{WELCOME_EMAIL}, {OFFICE_EMAIL}"
    )
    msg["subject"] = subject

    _attach_pdfs(msg, parsed["attachments"])

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail_service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
