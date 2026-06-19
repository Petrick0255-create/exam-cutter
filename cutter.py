import fitz
from PIL import Image
import io
import os
import re
import zipfile
import shutil

SCALE = 3
TOP_MARGIN = 50
BOTTOM_MARGIN = 20
LEFT_MARGIN = 25


def cut_exam(pdf_path):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    output_dir = os.path.join("output", pdf_name)

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    pdf = fitz.open(pdf_path)

    questions = []

    for page_num in range(len(pdf)):
        page = pdf[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()

                    if (
    re.fullmatch(r"(?:[1-9]|1[0-9]|2[0-5])\.", text)
    and span["bbox"][0] < 500
    and span["size"] >= 9
):
                        questions.append({
                            "number": int(text[:-1]),
                            "page": page_num,
                            "x": span["bbox"][0],
                            "y": span["bbox"][1]
                        })

    questions.sort(key=lambda q: q["number"])

    if not questions:
        pdf.close()
        raise Exception("문항 번호를 찾을 수 없습니다.")

    left_x_pdf = min(q["x"] for q in questions if q["x"] < 250)
    right_x_pdf = min(q["x"] for q in questions if q["x"] > 250)

    left_x = int(left_x_pdf * SCALE) - LEFT_MARGIN
    right_x = int(right_x_pdf * SCALE) - LEFT_MARGIN
    column_width = right_x - left_x

    for page_num in range(len(pdf)):
        page = pdf[page_num]

        pix = page.get_pixmap(
            matrix=fitz.Matrix(SCALE, SCALE),
            alpha=False
        )

        img = Image.open(io.BytesIO(pix.tobytes("png")))

        width, height = img.size

        page_questions = [q for q in questions if q["page"] == page_num]

        left_questions = sorted(
            [q for q in page_questions if q["x"] < 250],
            key=lambda q: q["y"]
        )

        right_questions = sorted(
            [q for q in page_questions if q["x"] > 250],
            key=lambda q: q["y"]
        )

        def crop_column(question_list, crop_x1):
            crop_x2 = min(width, crop_x1 + column_width)

            for idx, q in enumerate(question_list):
                start_y = max(
                    0,
                    int(q["y"] * SCALE) - TOP_MARGIN
                )

                if idx < len(question_list) - 1:
                    end_y = (
                        int(question_list[idx + 1]["y"] * SCALE)
                        - BOTTOM_MARGIN
                    )
                else:
                    end_y = height

                cropped = img.crop(
                    (
                        crop_x1,
                        start_y,
                        crop_x2,
                        end_y
                    )
                )

                filename = os.path.join(
                    output_dir,
                    f"{pdf_name}{q['number']:02d}.png"
                )

                cropped.save(filename)

        crop_column(left_questions, left_x)
        crop_column(right_questions, right_x)

    pdf.close()

    zip_path = os.path.join("output", f"{pdf_name}.zip")

    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for file in os.listdir(output_dir):
            full_path = os.path.join(output_dir, file)
            z.write(full_path, arcname=file)

    return zip_path