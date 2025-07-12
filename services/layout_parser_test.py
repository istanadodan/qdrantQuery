from typing import Dict, List, Optional, Union, Annotated
import requests
from dataclasses import dataclass
import io
from PIL import Image
import fitz  # pyMuPDF

# from markdown import markdownify as markdown

"""_summary_
  [document-parse]
    document-parse-250404	10 (Sync) / 30 (Async)

    1. 요구사항 분석 및 설계
        PyMuPDF(fitz): PDF 렌더링 및 영역 추출에 최적화된 라이브러리.
        Pillow: 이미지 후처리 및 저장에 활용.
        
        리팩토링 포인트:
        함수화 및 파라미터화로 재사용성 강화.
        예외처리로 안정성 확보.
        DPI(해상도) 및 좌표계 변환에 대한 명확한 처리.
        확장성(여러 영역, 여러 페이지, 포맷 옵션 등) 고려.
"""
from pathlib import Path
from pydantic import validate_call, FilePath, PositiveInt, Field
from typing import Annotated


# 사용 예시 (실제 파일 경로와 좌표 필요)
# pdf_path = 'sample.pdf'
# page_number = 0
# rect = (100, 100, 400, 300)  # PDF 포인트 단위 좌표
# output_path = 'capture.png'
# capture_pdf_region(pdf_path, page_number, rect, output_path)
@validate_call
def capture_pdf_region(
    page: object,
    id: int,
    page_number: PositiveInt,
    rect: Annotated[list[float], Field(min_length=4, max_length=4)],
    output_path: str,
    zoom: Annotated[float, Field(gt=0)] = 1.0,
) -> str:
    """
    PDF 파일의 특정 페이지에서 지정한 영역(rect)을 캡처하여 이미지로 저장합니다.

    Args:
        pdf_path (str): PDF 파일 경로
        page_number (int): 캡처할 페이지 번호 (0-based)
        rect (tuple): (x0, y0, x1, y1) 좌표 (포인트 단위, PDF 좌상단 기준)
        output_path (str): 저장할 이미지 파일 경로
        zoom (float): 확대 비율 (기본 2, 즉 144dpi)

    Returns:
        output_path (str): 저장된 이미지 경로

    # 검토 및 리팩토링 아이디어:
    # - 함수화로 재사용성 강화
    # - 예외처리로 안정성 확보
    # - 확대 비율(zoom) 파라미터화로 해상도 조절 가능
    # - 좌표계 변환 주의 (PDF는 포인트, Pillow는 픽셀)
    # - 여러 영역/페이지 반복처리 확장 가능
    # - 이미지 포맷 선택 옵션 추가 가능
    """

    filename = Path(output_path) / f"capture_{page_number}_{id:2d}.png"

    try:
        width, height = page.rect.width, page.rect.height
        # 확대 비율 적용(고해상도 추출)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes()))
        # 좌표 변환: 확대비율적용(포인트 -> 픽셀)
        x0, x1 = (int(r * zoom * width) for r in (rect[0], rect[2]))
        y0, y1 = (int(r * zoom * height) for r in (rect[1], rect[3]))
        region = img.crop((x0, y0, x1, y1))
        region.save(filename)
        return filename
    except Exception as e:
        print(f"Error: {e}")
        return ""


@dataclass
class Element:
    bounding_box: List[Dict[str, int]]
    category: str
    html: str
    id: int
    page: int
    text: str


def getPDFJson(file_path: str) -> list[dict]:
    """
    .content
    .elements
    00:
    {'category': 'heading1', 'content': {'html': "<h1 id='0' style='font-size:20px'>Multi-Page<br>Report</h1>", 'markdown': '', 'text': ''}, 'coordinates': [{...}, {...}, {...}, {...}], 'id': 0, 'page': 1}
    """
    import json

    api_key = "up_5BrLz2EBFUfqtpbekth5PW4aUwwyN"  # ex: up_xxxYYYzzzAAAbbbCCC
    # filename = "docs/sample-report.pdf"  # ex: ./image.png

    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"document": open(file_path, "rb")}
    data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse"}
    response = requests.post(url, headers=headers, files=files, data=data)

    return [
        dict(
            **d,
            html=d["content"]["html"] if "html" in d["content"] else "",
            rect=(
                *tuple(d["coordinates"][0].values()),
                *tuple(d["coordinates"][2].values()),
            ),
        )
        for d in response.json()["elements"]
        if d["category"] in ("figure", "chart", "table")
    ]


# 호출 예시
if __name__ == "__main__":
    import os

    # 실제 파일 경로, 페이지, 좌표, 저장 경로를 지정해야 함
    pdf_path = "mnt/docs/sample-report.pdf"

    # 출력 폴더
    output_path = "mnt/docs/output"
    os.makedirs(output_path, exist_ok=True)

    # 파일 읽어들임
    doc = fitz.open(pdf_path)

    elements: list[dict] = getPDFJson(pdf_path)

    for element in elements:
        page_number = element["page"]
        page = doc.load_page(page_number - 1)
        content = element["html"]
        id = element["id"]
        rect = element["rect"]
        result = capture_pdf_region(page, id, page_number, rect, output_path, zoom=1.0)
        print("저장 결과:", result, ", html:", content)
