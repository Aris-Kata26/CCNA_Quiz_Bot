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
    url = "https://polar-forest-95759-e6c7774f6065.herokuapp.com/api/random/"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raises error for 404/500
        json_data = response.json()

        if not json_data or not isinstance(json_data, list):
            return ("⚠️ Invalid API response.", None)

        qs = "📘 **Question:**\n" + json_data[0]['title'] + "\n\n"
        answer = None

        for idx, item in enumerate(json_data[0]['answer'], start=1):
            qs += f"{idx}. {item['answer']}\n"
            if item.get('is_correct'):
                answer = idx

        return (qs, answer) if answer else ("⚠️ No correct answer found.", None)

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return ("⚠️ Could not fetch question. Try again later.", None)
    
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