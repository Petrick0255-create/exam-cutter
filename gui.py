import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
from cutter import cut_exam


def select_pdfs():
    pdf_paths = filedialog.askopenfilenames(
        title="PDF 파일 선택",
        filetypes=[("PDF files", "*.pdf")]
    )

    if not pdf_paths:
        return

    try:
        status_label.config(text="문항 추출 중...")
        root.update()

        if len(pdf_paths) == 1:
            zip_path = cut_exam(pdf_paths[0])
            messagebox.showinfo(
                "완료",
                f"추출 완료!\n\n저장 위치:\n{zip_path}"
            )

        else:
            final_zip_path = os.path.join("output", "문항추출결과.zip")

            if os.path.exists(final_zip_path):
                os.remove(final_zip_path)

            created_zips = []

            for pdf_path in pdf_paths:
                zip_path = cut_exam(pdf_path)
                created_zips.append(zip_path)

            with zipfile.ZipFile(final_zip_path, "w", zipfile.ZIP_DEFLATED) as final_zip:
                for zip_path in created_zips:
                    folder_name = os.path.splitext(os.path.basename(zip_path))[0]

                    with zipfile.ZipFile(zip_path, "r") as z:
                        for name in z.namelist():
                            final_zip.writestr(
                                f"{folder_name}/{name}",
                                z.read(name)
                            )

            messagebox.showinfo(
                "완료",
                f"여러 PDF 추출 완료!\n\n저장 위치:\n{final_zip_path}"
            )

        status_label.config(text="완료")

    except Exception as e:
        status_label.config(text="오류 발생")
        messagebox.showerror(
            "오류",
            str(e)
        )


root = tk.Tk()
root.title("문항 추출기")
root.geometry("400x220")

title_label = tk.Label(
    root,
    text="PDF 문항 추출기",
    font=("맑은 고딕", 18, "bold")
)
title_label.pack(pady=20)

desc_label = tk.Label(
    root,
    text="PDF를 선택하면 문항별 PNG를 ZIP으로 저장합니다.",
    font=("맑은 고딕", 10)
)
desc_label.pack(pady=5)

select_button = tk.Button(
    root,
    text="PDF 선택",
    font=("맑은 고딕", 14),
    width=20,
    command=select_pdfs
)
select_button.pack(pady=20)

status_label = tk.Label(
    root,
    text="대기 중",
    font=("맑은 고딕", 10)
)
status_label.pack(pady=5)

root.mainloop()