import os
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from io import BytesIO

from reportlab.pdfgen import canvas

FILE_SAVE_PATH = '/Users/kakao/dev/finance/files'
OUTPUT_PATH = '/Users/kakao/dev/finance/files/result'
OUTPUT_PDF_PATH = '/Users/kakao/dev/finance/files/result/combined.pdf'


def _add_date_to_image_in_memory(image_path, user_text):
    """
    이미지에 날짜 텍스트를 추가하고, 메모리 상에서 처리.

    Args:
        image_path (str): 이미지 파일 경로.
        user_text (str): 삽입할 날짜 텍스트.

    Returns:
        BytesIO: 수정된 이미지를 PDF로 변환한 BytesIO 객체.
    """
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)

        # 폰트 설정
        try:
            font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", size=25)  # mac OS 폰트를 명시적으로 지정
        except OSError:
            font = ImageFont.load_default()  # 기본 폰트로 대체

        # 텍스트 크기 계산 (textbbox 사용)
        text_bbox = draw.textbbox((0, 0), user_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # 텍스트 위치 설정 (왼쪽 하단)
        x = 30  # 왼쪽 여백
        y = img.height - text_height - 30  # 이미지 높이에서 텍스트 높이와 하단 여백을 뺌

        draw.text((x, y), user_text, fill="red", font=font)

        # 이미지를 PDF로 변환하여 메모리 버퍼에 저장
        output = BytesIO()
        img.save(output, format="PDF")
        output.seek(0)
        return output


def merge_files_to_pdf(directory, output_pdf):
    """
    특정 디렉터리의 pdf, jpeg, png 파일을 디렉터리 순서대로 하나의 PDF로 병합하고 날짜 추가.

    Args:
        directory (str): 디렉터리 경로.
        output_pdf (str): 생성될 PDF 경로.
    """
    merger = PdfMerger()

    try:
        # 디렉터리에 있는 파일 순서대로 정렬
        for file_name in sorted(os.listdir(directory)):
            print(f"Processing file: {file_name}")
            file_path = os.path.join(directory, file_name)
            # date = file_name.split("-")[0]
            idx = '-'.join(file_name.split('-')[:-1])

            # PDF 파일 처리
            if file_name.endswith(".pdf"):
                updated_pdf = _add_date_to_pdf_in_memory(file_path, idx)
                merger.append(updated_pdf)

            # 이미지 파일 처리 (JPEG, PNG)
            elif file_name.lower().endswith((".jpeg", ".jpg", ".png")):
                updated_image_pdf = _add_date_to_image_in_memory(file_path, idx)
                merger.append(updated_image_pdf)

        # 병합된 PDF 저장
        with open(output_pdf, "wb") as f:
            merger.write(f)

        print(f"Combined PDF saved to: {output_pdf}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        merger.close()


def _add_date_to_pdf_in_memory(input_pdf, user_text, position=(50, 50)):
    """
    기존 PDF에 텍스트를 추가하고, 메모리 상에서 처리.

    Args:
        input_pdf (str): 원본 PDF 파일 경로.
        user_text (str): 추가할 텍스트.
        position (tuple): 텍스트 위치 (x, y 좌표).

    Returns:
        BytesIO: 텍스트가 추가된 PDF를 저장한 BytesIO 객체.
    """
    output = BytesIO()
    writer = PdfWriter()

    # 원본 PDF 읽기
    reader = PdfReader(input_pdf)

    for page in reader.pages:
        # 텍스트 오버레이 생성
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
        c.setFillColor("red")
        c.drawString(position[0], position[1], user_text)
        c.save()

        # 새 텍스트를 PDF로 변환
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        # 기존 페이지와 오버레이 병합
        page.merge_page(overlay_page)
        writer.add_page(page)

    # 결과 PDF를 메모리에 저장
    writer.write(output)
    output.seek(0)
    return output


if __name__ == "__main__":
    # make dir
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # 병합 실행
    merge_files_to_pdf(FILE_SAVE_PATH, OUTPUT_PDF_PATH)
