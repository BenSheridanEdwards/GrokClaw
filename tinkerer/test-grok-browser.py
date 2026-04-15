#!/usr/bin/env python3
"""Test browser-use Agent with Grok to fill a name field and upload CV on the Stationed form."""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from browser_use import Agent, Browser
from browser_use.llm.openai.like import ChatOpenAILike

APPLICATION_URL = "https://jadan.zo.space/ai-tinkerer/apply"
CV_PATH = str((Path(__file__).resolve().parent / "BenSheridanEdwards-CV-2026.pdf"))

llm = ChatOpenAILike(
    model="grok-3-fast",
    base_url="https://api.x.ai/v1",
    api_key=os.environ["XAI_API_KEY"],
)

task = f"""Navigate to {APPLICATION_URL}.
Find the Name field and type "Test Tinkerer Agent" into it.
Upload the CV file at: {CV_PATH}
Do NOT fill any other fields. Do NOT click Submit.
After uploading the file, scroll down to the file upload section so the attached file is visible on screen, then wait 5 seconds.
Report what you see on the page."""


async def main():
    browser = Browser(headless=False)
    agent = Agent(task=task, llm=llm, browser=browser, available_file_paths=[CV_PATH])
    history = await agent.run(max_steps=10)
    print("\n=== RESULT ===")
    print(history.final_result())
    print("=== DONE ===")
    await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
