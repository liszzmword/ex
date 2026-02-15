# Weekly Naver Real Estate Email Agent

월요일마다 아래 단지의 네이버부동산 매물과 최근 실거래 정보를 정리해서 `liszzm@skku.edu`로 보내는 에이전트입니다.

- 안양시 만안구 현대아파트
- 안양시 동안구 부영아파트

## 동작 방식

1. 네이버부동산 검색 API로 대상 단지를 찾습니다.
2. 단지 매물 API로 매매/전세/월세 매물을 수집합니다.
3. 실거래 API에서 최근 월별 거래 정보를 가져옵니다.
4. 텍스트 리포트를 이메일로 전송합니다.
5. GitHub Actions 스케줄러가 매주 월요일(한국시간 기준) 자동 실행합니다.

## 환경변수

`.env.example` 참고:

- `SMTP_HOST`
- `SMTP_PORT` (기본 587)
- `SMTP_USER`
- `SMTP_PASSWORD`
- `MAIL_FROM` (미설정 시 `SMTP_USER` 사용)
- `MAIL_TO` (기본 `liszzm@skku.edu`)

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python naver_real_estate_agent.py
```

## GitHub Actions 설정

Repository Settings → Secrets and variables → Actions에 아래 시크릿을 등록하세요.

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `MAIL_FROM` (선택)
- `MAIL_TO` (선택)

워크플로 파일: `.github/workflows/weekly_naver_realestate.yml`
