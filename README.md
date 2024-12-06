# FastAPI Kakao Login Integration

FastAPI를 사용하여 카카오 소셜 로그인, 로그아웃 기능을 구현합니다. 
사용자는 카카오 계정을 통해 애플리케이션에 로그인할 수 있으며, 액세스 토큰을 사용하여 사용자의 프로필 정보에 접근할 수 있습니다.

## 기능

- 카카오 인증을 통한 로그인
- 카카오 로그아웃
- 카카오 사용자 프로필 정보 접근
- 액세스 토큰 갱신

## 설치

프로젝트에 필요한 패키지를 설치합니다

```bash
pdm install
pip install itsdangerous
```
## 환경 설정

`.env` 파일을 생성하고 다음 환경 변수를 설정합니다:

```makefile
KAKAO_CLIENT_ID=your_kakao_client_id 
KAKAO_CLIENT_SECRET=your_kakao_client_secret 
KAKAO_REDIRECT_URI=your_kakao_redirect_uri  
KAKAO_LOGOUT_REDIRECT_URI=your_kakao_logout_redirect_uri
```

## 실행

애플리케이션을 실행하기 위해 다음 명령어를 사용합니다:

`uvicorn src.final_login.app:app --port 3000 --reload`

## 사용 방법    

웹 브라우저를 열고 `http://localhost:3000`으로 이동하여 로그인 페이지를 확인합니다. 카카오 로그인 버튼을 클릭하여 카카오 인증을 진행합니다.

인증이 성공하면 프론트엔드로 인가코드를 포함한 링크를 리턴합니다. 
프론트에서 인가코드를 포함한 링크로 액세스 토큰을 요청하면 카카오 API를 통해 엑세스 토큰을 얻어 프론트엔드로 반환합니다.

현재 코드에서는 프론트엔드에게 직접 data를 보낼 수 없는 오류를 해결하기 위해 redirect url을 callback에서 리턴하며, 무한 리다이렉트 됩니다. 
따라서 프론트엔드에서 별도의 리다이렉트 처리가 필요합니다. 

## 참고 자료

- FastAPI 공식 문서
- 카카오 로그인 REST API 가이드

---
