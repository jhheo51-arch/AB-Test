# OEM 실제 데이터 확보·적용 범위

저자: 허재혁. 실제 공개 OEM 자료와 CRM A/B 실험 원자료를 구분한다. 원본은 scratch에만 보관했고 상업적 재이용·재배포 권리는 아직 검토 전이다.

## 직접 재확인·다운로드한 자료
### 현대자동차 공식 모델별 판매 XLSX
- 공식 페이지: https://www.hyundai.com/worldwide/en/company/ir/ir-resources/sales-results
- 직접 페이지 본문과 다운로드 버튼 경로 확인, 2026년 10월 모델별 판매 XLSX 다운로드 성공.
- XLSX 압축 무결성, 워크북 이름 Unit Sales by Model, 월별·모델별 초기 셀 확인. 상세 출처·해시는 OEM_SOURCE_ACCESS_CHECK.json.
- 사용 후보: 모델 구성·월별 판매 변화·사업 환경을 이해하는 배경 사례.
- 한계: 집계 판매이며 개인 CRM 발송·노출·실험 배정·거래 연결 자료가 아니다. 판매 변화의 원인을 특정 캠페인 효과로 해석할 수 없다. 도매·소매·출고·등록의 정의를 구분해야 한다. 미래·미집계 월의 빈 셀을 0으로 바꾸지 않는다.

### Toyota Sustainability Data Book 2025
- 공식 PDF: https://global.toyota/pages/global_toyota/sustainability/report/sdb/sdb25_en.pdf
- 직접 다운로드·PDF 형식 확인 후 문서 텍스트 열람.
- 인쇄 쪽수 102: 애프터서비스의 네 축, 안전·품질·판매량·이익의 우선순위, 리콜 집계.
- 인쇄 쪽수 103 Customer Feedback System: 고객 문의 유형·고객센터 피드백 흐름·고객만족 설문 발송 및 응답·추천 평가 분포 확인.
- FY2025 일본 Toyota Customer Assistance Center 문의 263,000건, 설문 발송 9,063건·응답 1,144건 표기 확인. 이 숫자는 공개 보고의 범위에만 해당한다.
- 사용 후보: 서비스·고객 의견·설문 선택 편향·만족도와 사업 가치의 구분·딜러 협업을 질문하는 실제 산업 사례.
- 한계: 고객별 원자료나 무작위 배정 실험 아님. 설문 발송은 캠페인 도달이 아니며 추천 평가를 검증 없이 NPS·계약 전환으로 대체하지 않는다. 응답자의 평가를 전체 고객 평가로 단정하지 않는다.

## 조사 후보: 파일 확보/필드 검증 미완료
- 국토교통부 등록 통계: https://www.data.go.kr/data/15024777/fileData.do — 실제 행정 집계. 등록 재고와 신규 판매를 구분한다. 원파일·세부 이용 조건 확인 대기.
- NHTSA ODI 불만 기록: https://catalog.data.gov/dataset/nhtsas-office-of-defects-investigation-odi-complaints — 정부 접수 불만. 개별 신고 기록 후보이며 OEM 내부 CRM 원장 아님. ZIP·필드·개인정보 처리·이용 조건 확인 대기. 신고 건수를 모집단 분모 없이 불만률로 비교하지 않는다.
- Tesla 생산·인도 공식 발표: https://ir.tesla.com/press-release/tesla-third-quarter-2026-production-deliveries-and-deployments — 공식 검색 결과 수준 후보. 고객별 캠페인 실험이 아닌 분기 집계이며 원파일 확인 대기.

## 데이터 연결 원칙
실제 집계자료는 기업 맥락과 공개 사실 평가에만 사용한다. 실제 기업의 비공개 전환율·원가·군별 성과를 그럴듯하게 보간하지 않는다.
JH Motors 합성 실험은 별도 기업·별도 표기·별도 데이터다. 공시를 참고한 가정은 출처와 변환 가정을 명시하고, 실제 개인 로그로 소개하지 않는다.
고객별 CRM A/B 배정+반응+판매를 모두 갖춘 공개 OEM 데이터는 이번 조사에서 확보하지 못했다. 부재를 증명한 것은 아니다.
