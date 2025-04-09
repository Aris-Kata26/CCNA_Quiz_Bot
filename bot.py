import discord
import requests 
import json
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define intents
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def get_question():
    try:
        response = requests.get(
            "https://polar-forest-95759-e6c7774f6065.herokuapp.com/api/random/",
            timeout=5
        )
        response.raise_for_status()
        json_data = response.json()
        
        # Validate JSON structure
        if not json_data or not isinstance(json_data, list) or not json_data[0].get('answer'):
            raise ValueError("Invalid API response format")
            
        qs = "📘 **Question:**\n" + json_data[0]['title'] + "\n\n"
        answer = None
        
        for idx, item in enumerate(json_data[0]['answer'], start=1):
            qs += f"{idx}. {item['answer']}\n"
            if item.get('is_correct'):
                answer = idx
                
        if answer is None:
            raise ValueError("No correct answer found in response")
            
        return (qs, answer)

    except Exception as e:
        print(f"API Error: {str(e)}")
        return ("⚠️ Could not get a question. Please try again later.", None)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$question'):
        qs, answer = get_question()
        await message.channel.send(qs)

        if answer is None:
            return

        def check(m):
            return m.author == message.author and m.content.isdigit() and m.channel == message.channel

        try:
            guess = await client.wait_for('message', check=check, timeout=30.0)
            if int(guess.content) == answer:
                await message.channel.send('✅ Correct!')
            else:
                await message.channel.send(f'❌ Incorrect. The right answer was {answer}.')
        except asyncio.TimeoutError:
            await message.channel.send('⏰ Timeout!')

# Use token from environment variable
client.run(os.getenv('DISCORD_TOKEN'))