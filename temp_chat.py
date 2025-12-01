import asyncio, httpx

async def main():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/chat",
            json={"prompt": "Hola"},
        ) as r:
            print("Status:", r.status_code)
            data = []
            async for chunk in r.aiter_text():
                data.append(chunk)
            print("Body:", "".join(data))

asyncio.run(main())
