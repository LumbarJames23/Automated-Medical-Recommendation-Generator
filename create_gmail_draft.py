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
)
from utils import find_file_case_insensitive, load_text_file, title_case_words, region_verbose


def find_link_text(name: str) -> str | None:
    path = find_file_case_insensitive(HYPERLINKS_DIR, name)
    if not path:
        return None
    return load_text_file(path)


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


def create_gmail_draft(gmail_service, parsed, event_date):
    name = parsed["name"]
    date_line = event_date.strftime("%A, %B %d, %Y")
    subject = f"Dr. Mobin Recommendations - {name}"
    msg = MIMEMultipart()

    if not parsed["surg"]:
        header = load_template(NON_SURGICAL_TEMPLATE)
        body = render_placeholders(
            header,
            {
                "{$NAME}": name,
                "{$DATE}": date_line,
                "{$CLINIC_NAME}": CLINIC_NAME,
                "{$PHONE}": PHONE,
            },
        )

        pt = set(parsed["pt"])
        if pt:
            pt_text = "Physical Therapy of the "
            pt_text += "Cervical Spine and Lumbar Spine" if pt == {"CS", "LS"} else " and ".join(region_verbose(r) for r in pt)
            pt_text += " twice a week for 6 weeks."
            body += f"<li>{pt_text}</li>"

        if parsed["img"]:
            bullet = "<li>New Imaging:"
            if pt:
                bullet += " <b><i>Imaging is to be done only AFTER completion of physical therapy.</i></b>"
            bullet += "<ul>"
            for img, regs in parsed["img"].items():
                display_type = IMAGING_DISPLAY_NAMES.get(img.upper(), img)
                bullet += f"<li>{display_type} of the {', '.join(region_verbose(r) for r in regs)}</li>"
            bullet += "</ul></li>"
            body += bullet

        recs = parsed["recommendations"]
        if any(r.upper() == "HEP" for r in recs):
            body += "<li>Home Exercise Program</li>"

        for rec in recs:
            if rec.upper() == "HEP":
                continue

            text = recommendation_display_text(rec)
            pdf_target = RECOMMENDATION_RULES.get(rec.upper(), {}).get("pdf_name", rec)
            pdf_exists = find_file_case_insensitive(SUPPLEMENTS_DIR, pdf_target)
            link = find_link_text(rec) if not pdf_exists else None

            if link:
                body += f'<li><a href="{link}">{text}</a></li>'
            else:
                body += f"<li>{text}</li>"

        body += f"</ul><br>Please give our office a call at {PHONE} if you have any questions or concerns.<br>--"

    else:
        header = load_template(SURGICAL_TEMPLATE)
        body = render_placeholders(
            header,
            {
                "{$NAME}": name,
                "{$DATE}": date_line,
                "{$CLINIC_NAME}": CLINIC_NAME,
                "{$SURG}": parsed["surg"],
                "{$COORDINATOR_EMAIL}": COORDINATOR_EMAIL,
            },
        )

        if parsed["img"]:
            body += "Patient was also recommended to undergo new imaging prior to the surgery. Please see attached below for the order.<br><ul>"
            for img, regs in parsed["img"].items():
                display_type = IMAGING_DISPLAY_NAMES.get(img.upper(), img)
                body += f"<li>{display_type} of the {', '.join(region_verbose(r) for r in regs)}</li>"
            body += "</ul>"

        recs = parsed["recommendations"]
        if recs:
            body += "Dr. Mobin has also recommended the following:<br><ul>"
            if any(r.upper() == "HEP" for r in recs):
                body += "<li>Home Exercise Program</li>"
            for rec in recs:
                if rec.upper() == "HEP":
                    continue

                text = recommendation_display_text(rec)
                pdf_target = RECOMMENDATION_RULES.get(rec.upper(), {}).get("pdf_name", rec)
                pdf_exists = find_file_case_insensitive(SUPPLEMENTS_DIR, pdf_target)
                link = find_link_text(rec) if not pdf_exists else None

                if link:
                    body += f'<li><a href="{link}">{text}</a></li>'
                else:
                    body += f"<li>{text}</li>"
            body += "</ul><br>"

        body += f"Please give our office a call at {PHONE} if you have any questions or concerns.<br>--"

    msg.attach(MIMEText(body, "html"))
    msg["to"] = ""
    msg["cc"] = (
        f"{WELCOME_EMAIL}, {OFFICE_EMAIL}, {COORDINATOR_EMAIL}"
        if parsed["surg"]
        else f"{WELCOME_EMAIL}, {OFFICE_EMAIL}"
    )
    msg["subject"] = subject

    for f in parsed["attachments"]:
        try:
            with open(f, "rb") as fi:
                part = MIMEApplication(fi.read(), Name=os.path.basename(f))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(f)}"'
            msg.attach(part)
        except Exception:
            print(f"Error attaching file: {f}")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail_service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()