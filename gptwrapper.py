import asyncio
import html
import json
import re

import pandas as pd
from patchright.async_api import async_playwright,Page

async def smooth_scroll_to_end(page: Page, scroll_step: int = 200, delay: float = 0.1, pause: float = 2.0):
    # Get the initial page height
    previous_height = await page.evaluate("() => document.body.scrollHeight")
    while True:
        # Scroll down gradually in small steps
        for offset in range(0, previous_height, scroll_step):
            await page.evaluate(f"() => window.scrollTo(0, {offset})")
            await asyncio.sleep(delay)
        # Pause to allow new content to load
        await asyncio.sleep(pause)
        # Get the new page height after scrolling
        new_height = await page.evaluate("() => document.body.scrollHeight")
        # If the height hasn't changed, assume we've reached the bottom
        if new_height == previous_height:
            break
        previous_height = new_height



async def gptWrapper(inputText):
    df = pd.read_json("gpt.json")
    
    async with async_playwright() as p:
        browser =  await p.chromium.launch(
        
            
        
                          
        headless=False
    )  
        page = await  browser.new_page()
        await page.set_viewport_size({"width": 1280,"height": 720})
        
        page.set_default_timeout(31536000)
        
        url = "https://chatgpt.com/"
        
        await page.goto(url)
        await asyncio.sleep(0.5)
        decoded_text = html.unescape(inputText)
        # Escape special characters for safe JavaScript handling
        safe_input = json.dumps(decoded_text)
        await page.evaluate(f"""navigator.clipboard.writeText({safe_input})""")
        for i,row in df.iterrows():
                    if row["eventType"] =="MouseMove":
                    
                        #page.expect_navigation()
                        if df.iloc[i+1]["eventType"] =="MouseMove" and df.iloc[i+2]["eventType"] =="MouseMove"   :
                            continue
                        
                        match = re.search(r"X:\s*(\d+)\s*(?:,?\s*Y:\s*(\d+))?", row["details"])
                        if match:
                            x = int(match.group(1))
                            y = int(match.group(2)) if match.group(2) else None
                            
                            
                            await page.mouse.move(x,y)
                           

                    elif row["eventType"] =="MouseClick":
                     

                        #page.expect_navigation()
                        match = re.search(r"X:\s*(\d+)\s*(?:,?\s*Y:\s*(\d+))?", row["details"])

                        if match:
                            x = int(match.group(1))
                            y = int(match.group(2)) if match.group(2) else None
                            
                            await page.mouse.click(x,y)
                            await asyncio.sleep(1)
                            
                        
                            await page.keyboard.press('Control+V')
                            await asyncio.sleep(1)
                            await page.click("button[aria-label='Send prompt']")
                            
                            trig = await page.locator("div[class='min-w-9']").inner_text()
                            
                            while trig !="Voice":
                                await smooth_scroll_to_end(page=page,pause=0.1)
                                trig = await page.locator("div[class='min-w-9']").inner_text()

                            
                            
                            
                            res =await page.locator("div[data-message-author-role='assistant']").all_inner_texts()
                           
                            cleaned_data = res[0].strip().replace('\n', '').replace('\t', '')

                            
                            print(cleaned_data)
                            qA = {f"{inputText}":cleaned_data}

                    elif row["eventType"] == "KeyDown" and row["annotation"] == "type":
                    
                        match = re.search(r"Key:\s*Key(\w)", row["details"])

                        if match:
                            letter = match.group(1)
                        await page.keyboard.type(letter)
                        await asyncio.sleep(float(row["timeElapsed"]/1500))

                    elif row["eventType"] == "KeyDown" and row["annotation"] == "press":
                        
                        match = re.search(r"Key:\s*(\w+)", row["details"])

                        if match:
                            key_string = match.group(1)
                            await page.keyboard.press(key_string)
                            await asyncio.sleep(row["timeElapsed"]/1000)
                    
            
        with open("GPTQuestionAnswer.json", "w") as file:
                        json.dump(qA, file, indent=4)
        await asyncio.sleep(1)
        await browser.close()
     

if __name__ == "__main__":
    asyncio.run(gptWrapper("What is Lynx and what is its relation to react and flutter?"))
