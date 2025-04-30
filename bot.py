import discord
import requests
import asyncio
import os
import django
from dotenv import load_dotenv
from asgiref.sync import sync_to_async
from discord.ext import tasks
from datetime import datetime, timezone
timestamp=datetime.now(timezone.utc)

# Load environment variables
load_dotenv()

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ccnaquizbot.settings')
django.setup()

from discord.ext import commands
from ccnaquizbot.score.models import Score

@sync_to_async
def update_user_score(discord_id, username, points):
    """
    Update the user's score in the database.
    """
    print(f"Updating score for Discord ID: {discord_id}, Username: {username}, Points: {points}")  # Debug
    score, created = Score.objects.get_or_create(discord_id=discord_id, defaults={'name': username, 'point': 0})
    score.point += points
    score.name = username  # Update username in case it changes
    score.save()

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

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot with commands
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not post_daily_quiz.is_running():
        print("DEBUG - Starting post_daily_quiz task")
        post_daily_quiz.start()
    else:
        print("DEBUG - post_daily_quiz task is already running")

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
            guess = await bot.wait_for('message', check=check, timeout=60.0)
            if int(guess.content) == answer:
                points = 10  # Assign points for a correct answer (adjust as needed)
                await update_user_score(ctx.author.id, ctx.author.name, points)  # Await the async function
                await ctx.send(f'✅ Correct! You earned {points} points.\n📝 **Explanation:** {explanation}')
            else:
                await ctx.send(f'❌ Incorrect. The right answer was {answer}.\n📝 **Explanation:** {explanation}')
            # Update embed with correct answer
            embed.description = f"{qs}\n✅ **Correct Answer:** {answer}\n📝 **Explanation:** {explanation}"
            await question_message.edit(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send('⏰ Timeout!')
            # Update embed with timeout message
            embed.description = f"{qs}\n⏰ **Timed out.** Correct answer was {answer}\n📝 **Explanation:** {explanation}"
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

DAILY_QUIZ_CHANNEL_ID = int(os.getenv("DAILY_QUIZ_CHANNEL_ID"))

@tasks.loop(hours=24)  # Run this task every 24 hours
async def post_daily_quiz():
    """
    Posts a daily CCNA question in a specific channel and handles user responses.
    """
    # Fetch the channel
    channel = bot.get_channel(DAILY_QUIZ_CHANNEL_ID)
    if not channel:
        print(f"ERROR: Could not find channel with ID {DAILY_QUIZ_CHANNEL_ID}")
        return
    print(f"DEBUG - Found channel: {channel.name}")

    # Fetch a random question
    qs, answer, explanation, image_url = get_question(level=1)  # Default to Level 1 for daily quizzes

    # Create embed for the question
    embed = discord.Embed(
        title="📘 Daily CCNA Quiz",
        description=qs,
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)  # Use timezone-aware datetime
    )
    embed.set_footer(text="Answer by replying in this channel!")

    # Add image if available
    if image_url and isinstance(image_url, str) and image_url.lower().startswith(('http://', 'https://')):
        embed.set_image(url=image_url)

    # Post the question
    try:
        question_message = await channel.send(embed=embed)
        print("DEBUG - Successfully posted the daily quiz")
    except discord.errors.Forbidden:
        print("ERROR: Bot does not have permission to send messages in the channel")
        return
    except discord.errors.HTTPException as e:
        print(f"ERROR: Failed to send message: {e}")
        return

    # Wait for user responses
    def check(m):
        return m.channel == channel and m.content.isdigit() and not m.author.bot

    try:
        guess = await bot.wait_for('message', check=check, timeout=3600.0)  # Wait for 1 hour
        if int(guess.content) == answer:
            points = 5  # Assign points for the daily quiz
            await update_user_score(guess.author.id, guess.author.name, points)
            await channel.send(f"✅ {guess.author.mention}, Correct! You earned {points} points.\n📝 **Explanation:** {explanation}")
        else:
            await channel.send(f"❌ {guess.author.mention}, Incorrect. The correct answer was {answer}.\n📝 **Explanation:** {explanation}")
    except asyncio.TimeoutError:
        await channel.send("⏰ Time's up! No one answered the question.")
        embed.description += f"\n⏰ **Time's up!** The correct answer was {answer}.\n📝 **Explanation:** {explanation}"
        await question_message.edit(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))