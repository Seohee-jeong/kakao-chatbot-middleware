from fastapi import FastAPI, HTTPException, Request
import httpx

app = FastAPI()


@app.post("/apis/books")
async def proxy_books(request: Request):
    # 요청의 원시 데이터를 출력해 확인
    body = await request.body()
    print("Raw request body:", body)

    try:
        payload = await request.json()
    except Exception as e:
        print("JSON 파싱 에러:", e)
        raise HTTPException(status_code=400, detail="잘못된 JSON 데이터입니다.")

    external_url = "https://apps-script-144322417109.asia-northeast3.run.app/chat"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(external_url, json=payload)
        except httpx.HTTPError as e:
            print("외부 요청 에러:", e)
            raise HTTPException(
                status_code=502, detail=f"외부 서버 요청 중 오류 발생: {str(e)}"
            )

    external_data = response.json()
    response_data = {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": "간단한 텍스트 요소입니다."}}]
        },
    }
    return response_data
