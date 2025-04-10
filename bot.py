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

def get_question(level):
    url = f"https://polar-forest-95759-e6c7774f6065.herokuapp.com/api/random/?level={level}"
    print(f"DEBUG - Attempting to call URL: {url}") 
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raises error for 404/500
        json_data = response.json()

        if not json_data or not isinstance(json_data, list):
            return ("⚠️ Invalid API response.", None)

        # Extract question title and metadata
        question_data = json_data[0]  # Assuming the first item in the list is the question
        qs = f"📘 **Question:**\n{question_data['title']}\n\n"
        
        # Extract answers
        answer = None
        for idx, item in enumerate(question_data['answers'], start=1):
            qs += f"{idx}. {item['answer']}\n"
            if item.get('is_correct'):
                answer = idx

        # Include additional metadata (points, explanation, etc.)
        points = question_data.get('points', None)
        explanation = question_data.get('explanation', None)
        additional_metadata = question_data.get('additional_metadata', {})

        # Adding points and explanation to the message
        if points is not None:
            qs += f"\n💡 **Points:** {points}"

        if explanation:
            qs += f"\n📝 **Explanation:** {explanation}"

        if additional_metadata:
            # Example: Including category or hints from additional metadata
            category = additional_metadata.get('category', None)
            hint = additional_metadata.get('hint', None)
            if category:
                qs += f"\n📚 **Category:** {category}"
            if hint:
                qs += f"\n🔍 **Hint:** {hint}"

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

    if message.content.startswith('$ccna'):
        # Split the message into parts, e.g., "$ccna 1" -> ["$ccna", "1"]
        command_parts = message.content.split()

        # If the user provides a level (e.g., "$ccna 1"), the second part will be the level
        if len(command_parts) == 2 and command_parts[1].isdigit():
            level = int(command_parts[1])
            if level not in [1, 2, 3]:  # Only accept levels 1, 2, or 3
                await message.channel.send("⚠️ Invalid level. Please specify level 1, 2, or 3.")
                return
        else:
            await message.channel.send("⚠️ Please specify the CCNA level (1, 2, or 3).")
            return
        
        # Fetch the question based on the specified level
        qs, answer = get_question(level)
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
