from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from cutter import cut_exam
import shutil
import os
import zipfile
import uuid

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/")
async def home():
    html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>문제 추출기 | J&B LAB</title>

        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                min-height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: radial-gradient(circle at top, #0f1b3d, #050816 70%);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 28px;
            }

            .card {
                width: 520px;
                padding: 38px;
                border-radius: 28px;
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.14);
                box-shadow: 0 24px 70px rgba(0,0,0,0.4);
            }

            .top {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 26px;
            }

            .brand {
                font-size: 24px;
                font-weight: 900;
            }

            .badge {
                font-size: 13px;
                padding: 4px 8px;
                border: 1px solid #38bdf8;
                border-radius: 8px;
                color: #67e8f9;
                font-weight: 800;
            }

            h1 {
                font-size: 40px;
                margin-bottom: 14px;
                letter-spacing: -1px;
                background: linear-gradient(90deg, #7c3aed, #38bdf8, #2dd4bf);
                -webkit-background-clip: text;
                color: transparent;
            }

            p {
                color: #cbd5e1;
                line-height: 1.7;
                margin-bottom: 26px;
                font-size: 15px;
            }

            .notice {
                margin-bottom: 18px;
                padding: 13px 15px;
                border-radius: 14px;
                background: rgba(56,189,248,0.08);
                border: 1px solid rgba(56,189,248,0.20);
                color: #bae6fd;
                font-size: 13px;
                line-height: 1.5;
            }

            input[type="file"] {
                width: 100%;
                padding: 16px;
                margin-bottom: 18px;
                border-radius: 16px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                color: #e5e7eb;
            }

            button {
                width: 100%;
                padding: 16px;
                border: 0;
                border-radius: 16px;
                background: linear-gradient(90deg, #38bdf8, #2dd4bf);
                color: #020617;
                font-size: 17px;
                font-weight: 900;
                cursor: pointer;
                transition: 0.2s;
            }

            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 30px rgba(56,189,248,0.25);
            }

            .footer {
                margin-top: 22px;
                color: #64748b;
                font-size: 12px;
                text-align: center;
            }
        </style>
    </head>

    <body>
        <main class="card">
            <div class="top">
                <div class="brand">J&B</div>
                <div class="badge">LAB</div>
            </div>

            <h1>문제 추출기</h1>

            <p>
                PDF를 업로드하면 문항 번호를 기준으로<br>
                문제 이미지를 자동 추출해 ZIP 파일로 저장합니다.
            </p>

            <div class="notice">
                무료 서버라 첫 실행 시 30초~1분 정도 걸릴 수 있습니다.<br>
                평가원식 2단 PDF 기준으로 가장 안정적으로 작동합니다.
            </div>

            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="files" accept=".pdf" multiple required>
                <button type="submit">PDF 업로드하고 추출하기</button>
            </form>

            <div class="footer">
                © 2026 J&B LAB · Exam Cutter
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/upload")
async def upload_pdf(files: List[UploadFile] = File(...)):
    result_zip_name = f"문항추출결과_{uuid.uuid4().hex[:8]}.zip"
    result_zip_path = os.path.join(OUTPUT_DIR, result_zip_name)

    created_zips = []

    for file in files:
        save_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        zip_path = cut_exam(save_path)
        created_zips.append(zip_path)

    with zipfile.ZipFile(result_zip_path, "w", zipfile.ZIP_DEFLATED) as final_zip:
        for zip_path in created_zips:
            folder_name = os.path.splitext(os.path.basename(zip_path))[0]

            with zipfile.ZipFile(zip_path, "r") as z:
                for name in z.namelist():
                    final_zip.writestr(
                        f"{folder_name}/{name}",
                        z.read(name)
                    )

    return FileResponse(
        path=result_zip_path,
        media_type="application/zip",
        filename=result_zip_name
    )
