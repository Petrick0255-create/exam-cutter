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
    <html>
    <head>
        <meta charset="UTF-8">
        <title>문항 추출기</title>
    </head>
    <body>
        <h1>문항 추출기</h1>

        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="files" accept=".pdf" multiple required>
            <button type="submit">PDF 업로드</button>
        </form>
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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000
    )