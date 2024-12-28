"""
목적: local 에 저장된 영수증 파일을 읽어서, 필요한 컬럼만 추출하여 csv 파일로 저장하는 코드
"""

from domain.receipt.receipt_downloader import read_sheet, select_columns

SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CREDENTIAL_PATH = '/Users/kakao/dev/finance/secret/credential.json'
RECEIPT_SHEETS_ID = '1eFgcLV_mOkFlu92jOaq86lwrtzt3qvoUsLG9vT58KwE'
RECEIPT_SHEETS_PAGE = '설문지 응답 시트1'


if __name__ == '__main__':
    raw_data = read_sheet(RECEIPT_SHEETS_ID, RECEIPT_SHEETS_PAGE)
    selected_data = select_columns(raw_data)

    # 이차원 배열 한행을 excel 의 한 행으로 저장
    # 구매내역,청구비용,결재일자,비고
    # xlsx 파일로 저장
    import pandas as pd
    df = pd.DataFrame(selected_data[1:], columns=['구매내역', '청구비용', '결재일자', 'URL', '비고'])
    df = df.drop('URL', axis=1)
    df.to_excel('receipt.xlsx', index=False)








