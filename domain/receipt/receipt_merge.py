import os
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from io import BytesIO

FILE_SAVE_PATH = '/Users/kakao/dev/finance/test'
OUTPUT_PATH = '/Users/kakao/dev/finance/test/result'
OUTPUT_PDF_PATH = '/Users/kakao/dev/finance/test/result/combined.pdf'


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
            font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", size=40)  # mac OS 폰트를 명시적으로 지정
        except OSError:
            font = ImageFont.load_default()  # 기본 폰트로 대체

        # 텍스트 크기 계산 (textbbox 사용)
        text_bbox = draw.textbbox((0, 0), user_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # 텍스트 위치 설정 (오른쪽 하단)
        x = img.width - text_width - 30
        y = img.height - text_height - 30

        draw.text((x, y), user_text, fill="black", font=font)

        # 이미지를 PDF로 변환하여 메모리 버퍼에 저장
        output = BytesIO()
        img.save(output, format="PDF")
        output.seek(0)
        return output


def _add_date_to_pdf_in_memory(input_pdf, user_text):
    """
    PDF에 날짜 텍스트를 추가하고, 메모리 상에서 처리.

    Args:
        input_pdf (str): 원본 PDF 파일 경로.
        user_text (str): 삽입할 날짜 텍스트.

    Returns:
        BytesIO: 수정된 PDF를 저장한 BytesIO 객체.
    """
    output = BytesIO()
    writer = PdfWriter()

    # 원본 PDF 읽기
    reader = PdfReader(input_pdf)
    for page in reader.pages:
        # 텍스트 추가 (PyPDF2는 직접 텍스트 추가를 지원하지 않으므로 스킵)
        writer.add_page(page)

    # 수정된 PDF를 메모리로 저장
    writer.write(output)
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
            file_path = os.path.join(directory, file_name)
            date = file_name.split("-")[0]

            # PDF 파일 처리
            if file_name.endswith(".pdf"):
                updated_pdf = _add_date_to_pdf_in_memory(file_path, date)
                merger.append(updated_pdf)

            # 이미지 파일 처리 (JPEG, PNG)
            elif file_name.lower().endswith((".jpeg", ".jpg", ".png")):
                updated_image_pdf = _add_date_to_image_in_memory(file_path, date)
                merger.append(updated_image_pdf)

        # 병합된 PDF 저장
        with open(output_pdf, "wb") as f:
            merger.write(f)

        print(f"Combined PDF saved to: {output_pdf}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        merger.close()


if __name__ == "__main__":
    # make dir
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # 병합 실행
    merge_files_to_pdf(FILE_SAVE_PATH, OUTPUT_PDF_PATH)
