import asyncio
from crawl4ai import *
import pyperclip

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://ai.google.dev/gemini-api/docs/embeddings?hl=pt-br",
        )
        # Salva no clipboard
        pyperclip.copy(result.markdown)
        print("\nConteúdo salvo no clipboard!")

if __name__ == "__main__":
    asyncio.run(main())