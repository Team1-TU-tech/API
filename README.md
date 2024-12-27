# BACKEND API 

Kafka를 활용하여 백엔드 로그 데이터를 S3에 효율적으로 업로드하고, 이를 다양한 API 기능과 결합한 기능을 구현하였습니다.

## 주요 변경사항

### 1. Auth 백엔드 구현
- 자체 로그인, 로그아웃
- 카카오 로그인, 로그아웃
- 회원가입
- 위 기능에 대한 API 요청 및 응답을 로깅하는 기능 

### 2. 새로운 API 통합

기존의 여러 API를 하나로 통합
- search : 공연 제목, 카테고리, 날짜, 아티스트 이름, 지역으로 공연 정보 검색
- detail : MongoDB에 저장된 공연 정보를 `id` 기준으로 조회
- banner : 현재 날짜를 제외한 가장 가까운 공연 11개를 추출하여 메인 화면 배너에 표시
- top_show : 로그 데이터를 분석하여 가장 많이 클릭된 공연 상위 8개를 추출
- this_weekend : 현재 날짜를 기준으로 이번 주말에 볼 수 있는 공연 추출
- recommendation : ML 모델을 활용하여 description 분석 후 id에 해당하는 공연과 유사도가 가장 높은 3개 공연 추출
- exclusive
- popular

### 3. Kafka Consumer 
토픽 별로 메시지를 처리하고, 조건에 따라 S3에 데이터를 업로드하도록 로직 수정
- 1시간(3600초) 동안 한 토픽에 메시지가 쌓이면 자동 업로드
- 모든 토픽의 총 메시지가 1000개에 도달하면 즉시 업로드
- 업로드된 메시지는 메시지 카운트에서 제거하여 중복 업로드 방지

**Kafka 메시지 업로드 로직**
1시간(3600초) 동안 한 토픽에 메시지가 쌓이면 자동 업로드
모든 토픽의 총 메시지가 1000개에 도달하면 타이머를 무시하고 즉시 업로드
업로드된 메시지는 전체 메시지 카운트에서 제거되어 중복 업로드를 방지

Kafka 메시지 업로드 로직

첫 메시지가 수신되면 해당 토픽에 대해 3600초 타이머가 시작
3600초 동안 메시지가 쌓이면 해당 토픽의 데이터를 S3에 업로드
모든 토픽의 총 메시지가 1000개에 도달하면 타이머를 무시하고 즉시 업로드
업로드된 메시지는 전체 메시지 카운트에서 제거되어 중복 업로드를 방지
