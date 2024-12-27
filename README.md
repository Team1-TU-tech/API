# API
## 개요
- docker-compose를 활용하여 FastAPI 실행, 공연 정보 제공 
- 사용자가 다양한 공연에 대한 정보를 검색, 조회, 추천할 수 있도록 지원
- 사용자 경험을 향상시키기 위해 실시간 로그 데이터 분석 및 머신러닝 기반 추천 기능 제공
<br></br>
## 목차
- [기술스택](#기술스택)
- [개발기간](#개발기간)
- [API](#API)
- [실행요구사항](#실행요구사항)
- [Contributors](#Contributors)
- [License](#License)
- [문의](#문의)
  
<br></br>
## 기술스택
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=FastAPI&logoColor=FFFFFF"/> <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=Python&logoColor=F5F7F8"/> <img src="https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=MongoDB&logoColor=ffffff"/> <img src="https://img.shields.io/badge/Amazon%20S3-569A31?style=flat&logo=Amazon%20S3&logoColor=ffffff"/>
<br></br>
## 개발기간
`2024.11.28 ~ 2024.12.17(20일)`
<br></br>
## API 

![image](https://github.com/user-attachments/assets/ce4fc0a2-a098-4de2-8b38-a8d0eef3fa61)



### search
- 공연 제목, 카테고리, 날짜, 아티스트 이름, 지역으로 공연 정보 검색
- 검색 시 로그 생성 후 Kafka를 통해 S3에 업로드
### detail
- MongoDB에 저장된 공연 정보를 `id` 기준으로 조회
- 조회 시 로그 생성 후 Kafka를 통해 S3에 업로드
### banner
- 현재 날짜를 제외한 가장 가까운 공연 11개를 추출하여 메인 화면 배너에 표시
### popular
- S3에 저장된 로그 데이터를 분석
- 고유 `id`를 기준으로 조회 수를 집계한 뒤, 가장 많이 조회된 공연을 내림차순으로 정렬하여 MongoDB에 저장
- 저장된 데이터 중 인기 순으로 상위 8개의 공연 데이터를 추출
### this_weekend
- 현재 날짜를 기준으로 이번 주 주말(토요일 및 일요일)에 관람할 수 있는 공연 데이터를 추출
### auth
- **JWT 인증 방식**을 기반으로 자체 로그인 및 로그아웃 
  - 로그인: 사용자 정보 검증 후 `Access Token` 과 `Refresh Token` 을 발급
  - 로그아웃: 클라이언트 측에서 토큰 삭제(localStorage 처리) 방식으로 동작. 서버에서는 로그아웃 로그 생성을 위해 토큰 검증을 통해 사용자 ID를 추출
- 로그인/로그아웃 시 로그 생성 후 Kafka를 통해 S3에 업로드
### sign_up
- check-id: 사용자 ID 중복 여부를 MongoDB에서 조회
- signup: 사용자 정보를 검증하고 MongoDB에서 ID 중복 여부를 최종 확인한 뒤, 사용자 정보를 MongoDB에 저장
- 각 과정에서 발생하는 성공 또는 실패와 관련된 로그를 생성하여 Kafka를 통해 S3에 업로드
### kakao
- **카카오 API**를 사용하여 로그인, 로그아웃 및 사용자 정보를 관리
    - 로그인: 카카오 OAuth를 통해 사용자 인증 후 `Access Token`을 발급받고, MongoDB에 사용자 정보를 저장
    - 로그아웃: 카카오 로그아웃 API를 호출하여 사용자 세션을 종료
 - 로그인/로그아웃 시 로그 생성 후 Kafka를 통해 S3에 업로드
### recommendation
- ML 모델을 활용하여 MongoDB에 저장된 전체 데이터의 description을 분석한 후, 각 공연과 유사도가 가장 높은 공연 3개를 추출
- 추출된 데이터는 MongoDB에 저장
- 저장된 데이터에서 고유 `id`에 해당하는 공연과 유사도가 높은 상위 3개의 공연 정보를 함께 반환
### exclusive_main
- 단독 판매되는 공연을 예매처별로 4개씩 추출
### exclusive_all
- 예매처별 단독 판매되는 공연 전체 조회
<br></br>
## 실행 요구 사항 
```bash
# 도커 빌드
docker compose build

# 도커 백그라운드 실행
docker compose up -d
```
### FastAPI 접속
[localhost:8000](https://localhost:8000)

### Kafka UI 접속
[localhost:8081](https://localhost:8081)

## Contributors
`hahahellooo`, `hamsunwoo`, `oddsummer56`
<br></br>
## License
이 애플리케이션은 TU-tech 라이선스에 따라 라이선스가 부과됩니다.
<br></br>
## 문의
질문이나 제안사항이 있으면 언제든지 연락주세요:
<br></br>
- 이메일: TU-tech@tu-tech.com
- Github: `Mingk42`, `hahahellooo`, `hamsunwoo`, `oddsummer56`
