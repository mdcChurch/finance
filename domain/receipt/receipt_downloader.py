"""
1. google drive 접근
2. google drive 에서 url 을 읽어서 pdf, jpeg, png 파일로 local 에 저장
"""
import re

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

# 인증 및 Google Drive API 서비스 초기화
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive.readonly']
SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CREDENTIAL_PATH = '/Users/kakao/dev/finance/secret/credential.json'
RECEIPT_SHEETS_ID = '1eFgcLV_mOkFlu92jOaq86lwrtzt3qvoUsLG9vT58KwE'
RECEIPT_SHEETS_PAGE = '설문지 응답 시트1'
FILE_SAVE_PATH = '/Users/kakao/dev/finance/files'


def _authenticate_drive():
    creds = None
    if os.path.exists('token-for-drive.pickle'):
        with open('token-for-drive.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_PATH, SCOPES_DRIVE)
            creds = flow.run_local_server(port=0)
        with open('token-for-drive.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service


def _authenticate_sheets():
    creds = None
    # 이미 저장된 인증 정보가 있다면 사용
    if os.path.exists('token-for-sheets.pickle'):
        with open('token-for-sheets.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_PATH, SCOPES_SHEETS)
            creds = flow.run_local_server(port=0)
        # 인증 정보를 파일로 저장
        with open('token-for-sheets.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service


# Google Drive 파일 다운로드 함수
def _download_file(fid, d_path, f_path):
    try:
        # 1. Google Drive 서비스 초기화
        # TODO by 상후: 매번 초기화 하는게 맞을까?
        service = _authenticate_drive()

        # 2. 파일 메타데이터 가져오기
        file_metadata = service.files().get(fileId=fid, fields="name, mimeType").execute()
        file_name = file_metadata.get('name')  # 원래 파일 이름
        file_format = file_name.split('.')[-1]

        print(f"Downloading file: {file_name}")
        print(f"File descriptor: {file_format}")

        # 3. 디렉터리 생성 (필요시)
        if not os.path.exists(d_path):
            os.makedirs(d_path)  # 디렉터리 생성

        # 4. 파일 다운로드
        file_save_path = f"{f_path}.{file_format}"
        request = service.files().get_media(fileId=fid)
        with open(file_save_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")

        print(f"File saved to {file_save_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def read_sheet(sheet_id, range_name):
    service = _authenticate_sheets()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])

    if not values:
        print("No data found.")
        return []
    else:
        return values


def sheet_to_array(data):
    # ["구매내역", "청구비용", "결재일자", "URL"]
    selected_data = [[d[3], d[4], d[6], d[2]] for d in data[1:]]

    # 1. 날짜 전처리
    # yyyy.mm.dd 형식 결재 일자 기준으로 sort
    # 2024. 1. 5 을 2024.01.05 로 변경해야함.
    # 2024. 10. 1 을 2024.10.01 로 변경해야함.
    for i in range(len(selected_data)):
        date = selected_data[i][2].replace(" ", "").split('.')
        year = date[0]
        month = date[1]
        day = date[2]
        if len(month) == 1:
            month = '0' + month
        if len(day) == 1:
            day = '0' + day
        selected_data[i][2] = f"{year}.{month}.{day}"

    # 2024. 1. 28 이 2024. 1. 5 보다 앞서는 경우가 발생. 이건 날짜 포멧을 전처리해야한다.
    # 2024. 10. 1 이 2024. 2. 5 보다 앞서는 경우가 발생. 이건 날짜 포멧을 전처리해야한다.
    selected_data = sorted(selected_data, key=lambda x: x[2])

    # 2. 청구비용 전처리
    # 청구비용을 숫자로 변환 (, 원 제거)
    for i in range(len(selected_data)):
        selected_data[i][1] = int(re.sub(r'[원,A-Za-z]', '', selected_data[i][1]))

    # 헤더 더하기
    headers = ["구매내역", "청구비용", "결재일자", "URL"]
    selected_data.insert(0, headers)

    return selected_data


def downloader_from_sheet(data):
    for d in data[1:]:
        # case1. id 뒤에 fileId 가 있는 경우 'https://drive.google.com/open?id=abc'
        # case2. /d/ 뒤에 fileId 가 있는 경우 'https://drive.google.com/d/abc'
        # case3. 여러개의 url 이 한번에 있는 경우 'https://drive.google.com/open?id=abc, 'https://drive.google.com/open?id=abc2'

        # 로직
        # 1. url 을 , 로 split 한다.
        # 2. 각 url 에서 fileId 를 추출한다.
        # 2-1. case1&2 를 반영

        raw_url_field = d[3]
        urls = raw_url_field.split(',')

        for idx, url in enumerate(urls):
            if 'id=' in url:
                file_id = url.split('id=')[1]
            elif '/d/' in url:
                file_id = url.split('/d/')[1]
            else:
                raise ValueError(f"[downloader_from_sheet] Invalid URL, {url}")

            file_path = f"{FILE_SAVE_PATH}/{d[2]}-{d[0]}-{idx}"
            _download_file(file_id, FILE_SAVE_PATH, file_path)


if __name__ == '__main__':
    sheet_raw = read_sheet(RECEIPT_SHEETS_ID, RECEIPT_SHEETS_PAGE)
    sheet_data = sheet_to_array(sheet_raw)
    downloader_from_sheet(sheet_data)
