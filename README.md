# FastAPI JWT Authentication Implementation with Logging

FastAPI를 사용하여 **회원가입 기능**과 **JWT 인증 방식**을 이용한 **자체 로그인 시스템**을 구현합니다. 

회원가입 기능에서 사용자는 회원가입을 위해 필요한 정보를 입력하고, 데이터는 MongoDB에 저장됩니다.
또한, 회원가입 시 아이디 중복 체크를 포함한 기본적인 유효성 검사를 수행합니다.

자체 로그인 시스템은 JWT 인증 방식을 통해 사용자의 로그인, 로그아웃 및 JWT 토큰 발급과 갱신 기능을 포함하고 있으며, 로그인 성공 시 JWT를 반환받아 인증된 사용자만 접근할 수 있는 API를 사용할 수 있습니다.  
또한, 로깅 기능을 추가하여 인증된 API 엔드포인트를 호출할 때마다 로깅 기능이 활성화되어, 사용자의 API 호출 및 액세스 시도를 기록합니다.

## 기능

- 아이디 중복 체크: 회원가입 전에 사용자가 입력한 아이디가 이미 존재하는지 확인합니다.
- 회원가입: 사용자가 제공한 정보를 MongoDB에 저장합니다. 가입 시 자동으로 생성된 auth_id와 회원가입 시간(create_at)을 저장합니다.

- 사용자 로그인 (아이디, 비밀번호 기반)
- JWT 토큰을 이용한 인증
- 로그인 상태에서만 접근 가능한 API 엔드포인트
- 액세스 토큰 갱신 기능
- 인증 관련 이벤트 로깅 (로그인/로그아웃 시도, 성공/실패 등)

## 설치

프로젝트에 필요한 패키지를 설치합니다

```bash
pdm install
pip install .
```
## 환경 설정

`.env` 파일을 생성하고 다음 환경 변수를 설정합니다:

```makefile
SECRET_KEY=your_secret_key
MONGOPASS=your_mongodb_pw
ALGORITHM=your_algorithm

```
그 중 secret key는 secrets 모듈을 사용하여 랜덤생성한 키를 넣어주면 됩니다.
```
import secrets
secret_key = secrets.token_hex(32)
```

## 실행

애플리케이션을 실행하기 위해 다음 명령어를 사용합니다:

`uvicorn src.final_login.app:app --reload`

## 사용 방법    

웹 브라우저를 열고 `http://localhost:8000/docs`으로 이동하여 Swagger UI를 확인할 수 있습니다.

로그인 API를 테스트하려면 POST /login 엔드포인트를 호출하고, 요청 본문에 **username**과 **password**를 포함합니다.
로그인 성공 시 반환된 액세스 토큰을 사용하여 인증된 API 엔드포인트에 접근하고 로깅하여 이벤트를 기록합니다.

로그아웃 API를 테스트하려면 POST /logout 엔드포인트를 호출하여 로그아웃을 시도합니다. 
이 엔드포인트는 액세스 토큰을 사용하여 인증된 사용자의 세션을 종료하고, 로그아웃 이벤트를 기록합니다.
로그아웃 요청은 기본적으로 인증된 사용자만 접근할 수 있습니다. 따라서 로그아웃 요청 시, Authorization 헤더에 Bearer 토큰을 포함해야 합니다.

## 기타 정보
- MongoDB Atlas: MongoDB Atlas 클라우드 서비스를 사용하여 MongoDB를 호스팅합니다. 데이터베이스와 연결 정보를 .env 파일을 통해 관리합니다.
- FastAPI: 비동기 웹 프레임워크인 FastAPI를 사용하여 효율적인 API 서버를 구축합니다.
- CORS 설정: Frontend 스택인 React.js와 같은 다른 클라이언트 애플리케이션에서 API를 호출할 수 있도록 CORS 설정을 추가했습니다.

## 참고 자료

- FastAPI 공식 문서
---
