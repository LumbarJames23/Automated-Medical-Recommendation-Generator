import os
import time

from docx import Document
from docx2pdf import convert

from app_config import OUTPUT_ROOT, TEMPLATE_DIR


def _fill_template(template_path: str, save_path: str, name: str, dob: str, date_text: str) -> None:
    doc = Document(template_path)
    replacements = {"{$NAME}": name, "{$DOB}": dob, "{$DATE}": date_text}
    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)
    doc.save(save_path)
    time.sleep(0.3)
    convert(save_path, save_path.replace(".docx", ".pdf"))


def _generate_from_template(
    template_name: str, save_name: str, out_folder: str,
    name: str, dob: str, date_text: str
) -> None:
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    if not os.path.exists(template_path):
        print(f"Missing Template: {template_path}")
        return
    print(f"Generating: {template_name}")
    _fill_template(template_path, os.path.join(out_folder, save_name), name, dob, date_text)


def generate_documents(date, parsed: dict) -> None:
    out_folder = os.path.join(OUTPUT_ROOT, parsed["name"])
    os.makedirs(out_folder, exist_ok=True)
    today = date.strftime("%m.%d.%y")
    date_text = date.strftime("%m/%d/%Y")

    for img, regs in parsed["img"].items():
        for reg in regs:
            _generate_from_template(
                f"RX_{img}_{reg}_TEMPLATE.docx",
                f"RX {img} {reg} {today}.docx",
                out_folder, parsed["name"], parsed["dob"], date_text,
            )

    for reg in parsed["pt"]:
        _generate_from_template(
            f"RX_PT_{reg}_TEMPLATE.docx",
            f"RX PT {reg} {today}.docx",
            out_folder, parsed["name"], parsed["dob"], date_text,
        )
