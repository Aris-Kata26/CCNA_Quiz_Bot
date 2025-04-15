import discord
import requests
import asyncio
import os
from dotenv import load_dotenv
from discord.ext import commands
from ccnaquizbot.score.models import Score

def update_user_score(discord_id, username, points):
    """
    Update the user's score in the database.
    """
    score, created = Score.objects.get_or_create(discord_id=discord_id, defaults={'name': username, 'point': 0})
    score.point += points
    score.name = username  # Update username in case it changes
    score.save()
# Load environment variables
load_dotenv()

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot with commands
bot = commands.Bot(command_prefix='$', intents=intents)

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

        points = question_data.get('points')
        if points is not None:
            qs += f"\n💡 **Points:** {points}"

        image_url = question_data.get('image_url')
        print(f"DEBUG - Image URL from API: {image_url}")  # Debug log
        return (qs, answer, correct_explanation, image_url)

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return ("⚠️ Could not fetch question. Try again later.", None, None, None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='ccna')
async def ccna_quiz(ctx, level: int = None):
    if level not in [1, 2, 3]:
        await ctx.send("⚠️ Invalid level. Please specify level 1, 2, or 3. Example: `$ccna 2`")
        return

    qs, answer, explanation, image_url = get_question(level)
    
    # Create embed
    embed = discord.Embed(
        title="📘 Network Question",
        description=qs,
        color=discord.Color.blue()
    )
    
    # Set author info
    if ctx.author.avatar:
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.avatar.url
        )
    else:
        embed.set_author(name=ctx.author.display_name)
    
    # Add image if available
    if image_url and isinstance(image_url, str) and image_url.lower().startswith(('http://', 'https://')):
        print(f"DEBUG - Attempting to embed image: {image_url}")
        embed.set_image(url=image_url)
    else:
        print(f"DEBUG - Skipping image embed: image_url is {image_url}")

    embed.timestamp = ctx.message.created_at

    try:
        question_message = await ctx.send(embed=embed)
        
        if answer is None:
            return

        def check(m):
            return m.author == ctx.author and m.content.isdigit() and m.channel == ctx.channel

        try:
            guess = await bot.wait_for('message', check=check, timeout=30.0)
            if int(guess.content) == answer:
                await ctx.send('✅ Correct!')
            else:
                await ctx.send(f'❌ Incorrect. The right answer was {answer}.\n📝 **Explanation:** {explanation}')
            # Update embed with correct answer
            embed.description = f"{qs}\n✅ **Correct Answer:** {answer}"
            await question_message.edit(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send('⏰ Timeout!')
            # Update embed with timeout message
            embed.description = f"{qs}\n⏰ **Timed out.** Correct answer was {answer}"
            await question_message.edit(embed=embed)
            
    except discord.errors.HTTPException as e:
        print(f"Discord Embed Error: {e}")
        await ctx.send(qs)

@bot.command(name='leaderboard')
async def leaderboard(ctx):
    """
    Fetch and display the leaderboard from the Django API.
    """
    try:
        api_url = "http://127.0.0.1:8000/score/leaderboard/"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        leaderboard = response.json()

        if leaderboard:
            # Format the leaderboard for display
            leaderboard_message = "**🏆 Leaderboard:**\n"
            for rank, entry in enumerate(leaderboard, start=1):
                leaderboard_message += f"{rank}. {entry['name']} - {entry['points']} points\n"
            await ctx.send(leaderboard_message)
        else:
            await ctx.send("The leaderboard is currently empty. Be the first to score!")
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        await ctx.send("⚠️ Could not fetch the leaderboard. Please try again later.")

        
bot.run(os.getenv('DISCORD_TOKEN'))