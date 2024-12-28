from unittest import TestCase

from domain.receipt.receipt_downloader import select_columns


class Test(TestCase):
    def test_sheet_to_array(self):
        # given
        raw_data = [['타임스탬프', '안내 사항을 확인하셨나요? \U0001f979', '영수증 파일 첨부 부탁드립니다.', '구매 내역 ', '청구 비용 (원) ', '�입금 받을 계좌 정보 ',
                     '결제일자 ', '"구매 물품"이 기재된 영수증을 제출 하셨나요? ', '결제 일자 '],
                    ['2024. 1. 27 오후 10:45:38', '네', 'https://drive.google.com/open?id=a-vWgnB7zt', '카톡 메세지전송 / 포인트 충전',
                     '100,000', '신재호 국민 1-04-2', '2024. 1. 5'],
                    ['2024.   10. 30 오후 10:45:38', '네', 'https://drive.google.com/open?id=a-vWgnB7zt', '임원회의 간식 구매',
                     '200,000', '신재호 국민 1-04-2', '2024.10. 5']]

        # when
        data = select_columns(raw_data)

        # then
        # 1. header row 가 이와 같고 ["구매내역", "청구비용", "결재일자", "URL"]
        self.assertTrue(data[0][0] == "구매내역")
        self.assertTrue(data[0][1] == "청구비용")
        self.assertTrue(data[0][2] == "결재일자")
        self.assertTrue(data[0][3] == "URL")

        # 2. 구매내역에 `/` 가 없어야 한다.
        purchase_list = [d[0] for d in data[1:]]
        filtered_list = [p for p in purchase_list if '/' not in p]

        self.assertEqual(len(purchase_list), len(filtered_list))
