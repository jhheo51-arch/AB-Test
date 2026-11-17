# 공개 데이터 후보·접근 확인

## 확인 완료: Hillstrom / MineThatData 이메일 실험
원출처: https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html
공식 소개: https://www.tensorflow.org/datasets/catalog/hillstrom
원출처 설명: 최근 12개월 구매 고객을 남성 상품 이메일·여성 상품 이메일·무발송에 무작위 배정하고 2주 후 방문·구매·지출을 추적.
직접 CSV 다운로드·파싱 결과: 64,000행. 실제 컬럼과 그룹 수는 HILLSTROM_ACCESS_CHECK.json에 기록.
가능: 방문·구매·고객당 지출·무발송 대비 비교·사전 고객 속성 분석.
불가: 오픈율·클릭률·자동차 계약·출고·실제 원가·장기 LTV 분석. 해당 컬럼이 없다.
구분: 방문은 클릭이 아니고 지출은 이익이 아니다. 실험 데이터셋의 고객을 OEM 고객으로 바꿔 실제 자동차 데이터라고 부르지 않는다.
권리: 공개 분석용 제공은 확인했으나 상업 전자책 재사용·원본 재배포 조건은 아직 확인되지 않음. 원본은 로컬 scratch에만 보관하고 저장소에 커밋하지 않음. 웹페이지의 CC 표기를 데이터의 재배포 라이선스로 간주하지 않음.
접근 경고: HTTPS 원본은 인증서 검증 실패. 검증을 끄지 않고 원출처가 제공한 HTTP 주소로 다운로드함. HTTP 전송 무결성·출처 위변조 위험이 남으므로 독립 사본 대조 전에는 검증된 정본·확정 출간 데이터로 취급하지 않음. SHA-256은 받은 파일 식별용이지 진본 보증 아님.

## 검색으로 확인한 후보: 후속 원문·권리·파일 확인 필요
- 국토교통부 자동차 등록 현황: https://www.data.go.kr/data/15024777/fileData.do
  - 지역·차종 등 산업 배경 후보. 개인 CRM 실험 로그가 아님. 다운로드·스키마·이용 조건 검증 전.
- 한국교통안전공단 신규등록정보: https://www.data.go.kr/data/15059401/openapi.do
  - 등록 시점·차종·연료·권역 등 후보. API 이용 신청·인증과 제공 범위 확인 필요.
- Criteo uplift: https://ailab.criteo.com/criteo-uplift-prediction-dataset/
  - 광고 증분 실험·방문·전환 학습 후보. 대용량, OEM·이메일 오픈·매출 대체 아님. 원파일·약관 미검증.
- UCI Bank Marketing: https://archive.ics.uci.edu/dataset/222/bank+marketing
  - 캠페인 반응·고객 속성 학습 후보. 무작위 A/B 대조군이 확인된 실험으로 취급하지 않음. 원파일·라이선스 재검토 필요.
- Kaggle synthetic car sales: https://www.kaggle.com/datasets/jayavarman/synthetic-car-sales-dataset-over-million-records
  - 검색 결과에서부터 합성으로 명시. 실제 OEM 데이터 확보로 보고하지 않음. 채택하지 않음.

## 측정 근거
Apple Mail Privacy Protection 공식 설명:
https://www.apple.com/legal/privacy/data/en/mail-privacy-protection/
본문을 직접 확인: Protect Mail Activity는 이메일에 관여했는지와 무관하게 원격 콘텐츠를 기본적으로 백그라운드 다운로드한다. 따라서 추적 픽셀 기반 오픈을 실제 읽음과 동일하게 해석하지 않는다.

## 책의 데이터 전략
실제 공개 실험 = 현실 데이터의 변동·증분 효과를 다루는 보조 사례. 권리·진본 확인 후 출간 채택 여부 결정.
공공 자동차 통계 = 가상 기업의 배경 참고. 사용한 값과 가정값을 분리.
JH Motors 합성 = 지표 충돌·품질 오류·관측 지연 등 통제 가능한 진단 실습. 실제 기업 실적이라고 주장하지 않음.
현재 OEM의 발송·오픈·클릭·계약·매출·대조군이 모두 연결된 실제 공개 데이터는 확보하지 못했다. 찾지 못했다는 것이 존재하지 않는다는 뜻은 아니다.
