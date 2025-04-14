import discord
import requests 
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
        response.raise_for_status()
        question_data = response.json()

        if not question_data or not isinstance(question_data, dict):
            print("DEBUG - Invalid API response: not a dictionary")
            return ("⚠️ Invalid API response.", None, None, None)

        qs = f"📘 **Question:**\n{question_data['title']}\n\n"
        answer = None
        correct_explanation = None
        for idx, item in enumerate(question_data['answers'], start=1):
            qs += f"{idx}. {item['answer']}\n"
            if item.get('is_correct'):
                answer = idx
                correct_explanation = item.get('explanation', 'No explanation provided.')

        if answer is None:
            print("DEBUG - No correct answer found")
            return ("⚠️ No correct answer found.", None, None, None)

        points = question_data.get('points', None)
        if points is not None:
            qs += f"\n💡 **Points:** {points}"

        image_url = question_data.get('image_url', None)
        return (qs, answer, correct_explanation, image_url)

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return ("⚠️ Could not fetch question. Try again later.", None, None, None)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$ccna'):
        command_parts = message.content.split()
        if len(command_parts) == 2 and command_parts[1].isdigit():
            level = int(command_parts[1])
            if level not in [1, 2, 3]:
                await message.channel.send("⚠️ Invalid level. Please specify level 1, 2, or 3.")
                return
        else:
            await message.channel.send("⚠️ Please specify the CCNA level (1, 2, or 3).")
            return

        qs, answer, explanation, image_url = get_question(level)
        
        # Create embed regardless of whether there's an image
        embed = discord.Embed(
            title="📘 Network Question",
            description=qs,
            color=discord.Color.blue()
        )
        
        # Set author info
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.avatar.url if message.author.avatar else None
        )
        
        # Add image if available
        if image_url and isinstance(image_url, str) and image_url.startswith("http"):
            embed.set_image(url=image_url)
        
        embed.timestamp = message.created_at

        try:
            question_message = await message.channel.send(embed=embed)
        except discord.errors.HTTPException as e:
            print(f"Discord Embed Error: {e}")
            question_message = await message.channel.send(qs)

        if answer is None:
            return

        def check(m):
            return m.author == message.author and m.content.isdigit() and m.channel == message.channel

        try:
            guess = await client.wait_for('message', check=check, timeout=30.0)
            if int(guess.content) == answer:
                await message.channel.send('✅ Correct!')
            else:
                await message.channel.send(f'❌ Incorrect. The right answer was {answer}.\n📝 **Explanation:** {explanation}')
            await question_message.edit(content=f"{qs}\n✅ **Correct Answer:** {answer}")
        except asyncio.TimeoutError:
            await message.channel.send('⏰ Timeout!')
            await question_message.edit(content=f"{qs}\n⏰ **Timed out.** Correct answer was {answer}")

client.run(os.getenv('DISCORD_TOKEN'))