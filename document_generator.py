import os
import time

from docx import Document
from docx2pdf import convert

from app_config import OUTPUT_ROOT, TEMPLATE_DIR


def edit_template(path, repl, save):
    doc = Document(path)
    for p in doc.paragraphs:
        for k, v in repl.items():
            if k in p.text:
                p.text = p.text.replace(k, v)
    doc.save(save)
    time.sleep(0.3)
    convert(save, save.replace(".docx", ".pdf"))


def generate_documents(date, parsed):
    out_folder = os.path.join(OUTPUT_ROOT, parsed["name"])
    os.makedirs(out_folder, exist_ok=True)
    today, date_text = date.strftime("%m.%d.%y"), date.strftime("%m/%d/%Y")

    # Imaging templates
    for img, regs in parsed["img"].items():
        for reg in regs:
            template_name = f"RX_{'DXR' if img == 'DXR' else img}_{reg}_TEMPLATE.docx"
            template_path = os.path.join(TEMPLATE_DIR, template_name)
            if os.path.exists(template_path):
                print(f"Generating: {template_name}")
                save_path = os.path.join(out_folder, f"RX {img} {reg} {today}.docx")
                edit_template(
                    template_path,
                    {"{$NAME}": parsed["name"], "{$DOB}": parsed["dob"], "{$DATE}": date_text},
                    save_path,
                )
            else:
                print(f"Missing Template: {template_path}")

    # PT templates
    for reg in parsed["pt"]:
        template_name = f"RX_PT_{reg}_TEMPLATE.docx"
        template_path = os.path.join(TEMPLATE_DIR, template_name)
        if os.path.exists(template_path):
            print(f"Generating: {template_name}")
            save_path = os.path.join(out_folder, f"RX PT {reg} {today}.docx")
            edit_template(
                template_path,
                {"{$NAME}": parsed["name"], "{$DOB}": parsed["dob"], "{$DATE}": date_text},
                save_path,
            )
        else:
            print(f"Missing Template: {template_path}")