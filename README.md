# Auth Backend finish

auth 백엔드 구현 완료 (로그인, 로그아웃, 아이디 중복체크 , 회원가입)

FastAPI를 사용하여 회원가입 기능과 JWT 인증 방식을 이용한 자체 로그인 시스템 구현완료. 
사용자는 회원가입을 위해 필요한 정보를 입력하고, 데이터는 MongoDB에 저장. 
회원가입 시 아이디 중복 체크와 기본적인 유효성 검사를 수행.
JWT 인증을 통해 사용자의 로그인, 로그아웃 및 JWT 토큰 발급과 갱신 기능을 제공함.
또한, 로깅 기능을 추가하여 사용자의 API 호출 및 액세스 시도를 기록함.

## 기능
- 아이디 중복 체크: 회원가입 전에 사용자가 입력한 아이디가 이미 존재하는지 확인.
- 회원가입: 사용자가 제공한 정보를 MongoDB에 저장. 가입 시 자동으로 생성된 auth_id와 회원가입 시간(create_at)을 저장.
- 사용자 로그인 (아이디, 비밀번호 기반)
- JWT 토큰을 이용한 인증
- 액세스 토큰 갱신 기능 (refresh_token)
- 인증 관련 이벤트 로깅 (로그인/로그아웃 시도, 성공/실패 등)

## API 엔드포인트

### 1. login
#### 요청 예시
```
curl -X 'POST' \
  'http://127.0.0.1:8000/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "{id}",
  "password": "{password}"
}'
```

#### 응답 예시
- 로그인 성공

Response body
```
{
  "access_token": "{access_token}",
  "refresh_token": "{refresh_token}",
  "token_type": "bearer"
}
```
로깅 
```
{'timestamp': '2024-12-11T00:26:46.525686', 'user_id': 'jihyuno0730', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'Login', 'birthday': '2000-05-06', 'gender': 'F'}
```
- 로그인 실패

Response body
```
{
  "detail": "Invalid credentials"
}
```
로깅 
```
{'timestamp': '2024-12-11T00:26:09.829740', 'user_id': 'anonymous', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'User Validate failed', 'error': 'Invalid credentials or user not found'
```
### 2. logout
#### 요청 예시
```
curl -X 'POST' \
  'http://127.0.0.1:8000/auth/logout' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "{id}",
  "password": "{password}"
}'
```

#### 응답 예시
- 로그아웃 성공

Response body
```
{
  "message": "Logged out successfully"
}
```
로깅 
```
{'timestamp': '2024-12-11T00:30:58.747472', 'user_id': 'jihyuno0730', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'Logout'}
```
- 로그아웃 실패 

Response body
```
{
  "detail": "Invalid credentials"
}
```
로깅 
```
{'timestamp': '2024-12-11T00:26:09.829740', 'user_id': 'anonymous', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'User Validate failed', 'error': 'Invalid credentials or user not found'
```





### 3. check-id
#### 요청 예시
```
curl -X 'POST' \
  'http://127.0.0.1:8000/signup/check-id' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "{id}"
}'
```

#### 응답 예시
- 중복 아이디 있음

Response body
```
{
  "detail": "아이디가 이미 존재합니다."
}
```
로깅 
```
{'timestamp': '2024-12-11T01:57:50.941158', 'user_id': 'anonymous', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'CheckID', 'status': 'failed', 'error': 'ID already exists', 'requested_id': 'test', 'ip_address': '127.0.0.1'}
```
- 중복 아이디 없음

Response body
```
{
  "is_taken": false
}
```
로깅 
```
{'timestamp': '2024-12-11T01:58:33.002202', 'user_id': 'anonymous', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'CheckID', 'status': 'success', 'requested_id': 'tesaaat', 'ip_address': '127.0.0.1'}
```

### 4. signup
#### 요청 예시
```
curl -X 'POST' \
  'http://127.0.0.1:8000/signup/signup' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "{username}",
  "id": "{id}",
  "pw": "{pw}",
  "email": "{email}",
  "phoneNumber": "{phoneNumber}",
  "agreeMarketing": "{agreeMarketing}",
  "gender": "{gender}",
  "birthday": "{birthday}",
  "create_at": "string", # 아무것도 입력하지 않아도 저절로 입력됨
  "auth_id": "string"  # 아무것도 입력하지 않아도 저절로 입력됨
}'
```

#### 응답 예시
- 회원가입 성공

Response body
```
{
  "success": true
}
```
로깅 
```
{'timestamp': '2024-12-11T02:08:01.423860', 'user_id': 'anonymous', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'SignUp', 'status': 'success', 'requested_id': 'shine56', 'ip_address': '127.0.0.1'}
```
- 회원가입 실패

Response body
```
{
  "detail": "아이디가 이미 존재합니다."
}
```
로깅 
```
{'timestamp': '2024-12-11T02:13:41.355549', 'user_id': 'anonymous', 'device': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'action': 'SignUp ID check', 'status': 'failed', 'error': 'ID already exists', 'requested_id': 'shine56', 'ip_address': '127.0.0.1'}
```
