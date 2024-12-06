# FastAPI Sign up Integration

FastAPI를 사용하여 로그인 기능을 구현합니다.  
사용자는 회원가입을 위해 필요한 정보를 입력하고, 데이터는 MongoDB에 저장됩니다.   
또한 회원가입 시 아이디 중복 체크를 포함한 기본적인 유효성 검사를 수행합니다.

## 기능

- 아이디 중복 체크: 회원가입 전에 사용자가 입력한 아이디가 이미 존재하는지 확인합니다.
- 회원가입: 사용자가 제공한 정보를 MongoDB에 저장합니다. 가입 시 자동으로 생성된 auth_id와 회원가입 시간(create_at)을 저장합니다.

## 설치

프로젝트에 필요한 패키지를 설치합니다

```bash
pdm install
pip install .
```

## 환경 설정

`.env` 파일을 생성하고 다음 환경 변수를 설정합니다:

```makefile
MONGOPASS=your_mongodb_password
```

그 중 secret key는 secrets 모듈을 사용하여 랜덤생성한 키를 넣어주면 됩니다.
```
import secrets
secret_key = secrets.token_hex(32)
```

## 실행

서버를 실행하기 위해 다음 명령어를 사용합니다:

`uvicorn app:app --reload`

## 사용 방법    

웹 브라우저를 열고 `http://localhost:8000/docs` 에서 실행됩니다. 

## API 엔드포인트
### 1. 아이디 중복 체크 API
#### 요청 예시
```
curl -X POST "http://127.0.0.1:8000/check-id" -H "Content-Type: application/json" -d '{
  "id": "{checking_id}}"
}'
```

#### 응답 예시
- 존재하는 경우
```
{"detail":"아이디가 이미 존재합니다."}
```

- 존재하지 않는 경우
```
{"is_taken":false}
```

### 2. 회원가입 API
#### 요청 예시
```
curl -X POST "http://127.0.0.1:8000/signup" \
-H "Content-Type: application/json" \
-d '{
  "username": "{username}",
  "id": "{id}",
  "pw": "{password}",
  "email": "{email}",
  "phoneNumber": "{phone_number}",
  "agreeMarketing": "{true/false}",
  "gender": "{F/M}",
  "birthday": "{birthday}"
}'
```

#### 응답 예시
- 중복 아이디가 존재하는 경우
```
{"detail":"아이디가 이미 존재합니다."}
```

- 중복 아이디가 존재하지 않는 경우
```
{"success":true}
```

## 기타 정보 

- MongoDB Atlas: MongoDB Atlas 클라우드 서비스를 사용하여 MongoDB를 호스팅합니다. 데이터베이스와 연결 정보를 .env 파일을 통해 관리합니다.
- FastAPI: 비동기 웹 프레임워크인 FastAPI를 사용하여 효율적인 API 서버를 구축합니다.
- CORS 설정: Frontend 스택인 React.js와 같은 다른 클라이언트 애플리케이션에서 API를 호출할 수 있도록 CORS 설정을 추가했습니다.
---
