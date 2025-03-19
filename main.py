import asyncio
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
import httpx


app = FastAPI()
agent_space_url = "https://apps-script-144322417109.asia-northeast3.run.app/chat"


@app.post("/apis/check")
async def check(request):
    # 요청의 원시 데이터를 출력해 확인
    body = await request.body()
    print("[check] Raw request body:", body)


@app.post("/apis/books")
async def proxy_books(request: Request, background_tasks: BackgroundTasks):
    # 요청의 원시 데이터를 출력해 확인
    try:
        payload = await request.json()
        print("payload", payload)
        user_request = payload["userRequest"]
        request_payload = payload["action"]["params"]
        callback_url = user_request["callbackUrl"]

    except Exception as e:
        print("JSON 파싱 에러:", e)
        raise HTTPException(status_code=400, detail="잘못된 JSON 데이터입니다.")

    # 임시 응답을 3초 후에 먼저 반환
    callback_response = {
        "version": "2.0",
        "useCallback": True,
        "data": {"text": "답변을 입력중입니다 . . ."},
    }
    # 3초 내에 응답을 보내고, 나중에 비동기적으로 결과를 보냄
    background_tasks.add_task(handle_search_books, request_payload, callback_url)

    # 3초 후에 임시 응답을 반환
    return callback_response


async def search_books_from_agent_space(url: str, query: str):
    payload = {
        "query": query,
    }
    async with httpx.AsyncClient() as client:
        response_data = {
            "version": "2.0",
            "template": {"outputs": [{"simpleText": "잠시 뒤에 다시 시도해주세요."}]},
        }
        try:
            response = await client.post(url, json=payload)
        except httpx.TimeoutException as te:
            print("time out error", te)
            return response_data
        except httpx.HTTPError as e:
            print("외부 요청 에러:", e)
            return response_data

    external_data = response.json()

    carousel_item_list = []
    for item in external_data["items"]:
        carousel_item_list.append(
            {
                "title": item["title"],
                "description": f"""카테고리 : {item["category"]}\n도서 코드 : {item["call_no"]}""",
                "thumbnail": {"imageUrl": item["image"]},
            }
        )

    response_data = {
        "version": "2.0",
        "useCallback": True,
        "template": {
            "outputs": [
                {"simpleText": f"총 {len(carousel_item_list)}권의 도서를 찾았어요!"},
                {"carousel": {"type": "basicCard", "items": carousel_item_list}},
            ]
        },
    }

    return response_data


async def handle_search_books(request_payload, callback_url):
    print("handle_search_books")
    try:
        # search_books_from_agent_space가 시간이 오래 걸릴 수 있으므로 비동기 처리
        result = await search_books_from_agent_space(
            agent_space_url, request_payload["query"]
        )

        print("callback url : ", callback_url)
        print("result : ", result)
        # 결과를 kakao_callback으로 보내기
        await kakao_callback(callback_url, result)
    except Exception as e:
        print(f"Error during search: {e}")


async def kakao_callback(callback_url: str, result: dict):
    try:
        # 콜백 URL로 결과를 전송
        async with httpx.AsyncClient() as client:
            result = await client.post(callback_url, json=result)
            print("kakao_callback response status: ", result.status_code)
            print("kakao_callback response text: ", result.text)
    except httpx.RequestError as e:
        print(f"콜백 요청 오류 발생: {e}")
    except httpx.HTTPStatusError as e:
        print(f"콜백 HTTP 상태 오류 발생: {e}")
