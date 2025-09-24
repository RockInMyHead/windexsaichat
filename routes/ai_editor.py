import os
import openai
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()

@router.post("/api/ai-editor")
async def ai_editor(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model", "gpt-4")

    def event_stream():
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        for chunk in response:
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content")
            if content:
                yield content

    return StreamingResponse(event_stream(), media_type="text/event-stream")
