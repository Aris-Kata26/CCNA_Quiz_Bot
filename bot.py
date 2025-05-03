import discord  # Main library for interacting with the Discord API.
import requests  # For making HTTP requests to external APIs.
import asyncio  # For asynchronous programming.
import os  # For interacting with the operating system (e.g., environment variables).
import django  # For integrating Django models and database operations.
from dotenv import load_dotenv  # For loading environment variables from a `.env` file.
from asgiref.sync import sync_to_async  # For running Django ORM queries asynchronously.
from discord.ext import tasks, commands  # For creating tasks and bot commands.
from datetime import datetime, timezone  # For working with timestamps and time zones.
from PIL import Image, ImageDraw, ImageFont  # For creating flashcard images.
import io  # For handling in-memory file operations.
import random  # For selecting random motivational messages and reminders.


timestamp=datetime.now(timezone.utc)


# Load environment variables from the `.env` file.
load_dotenv()

# Set up Django settings for database integration.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ccnaquizbot.settings')
django.setup()

from discord.ext import commands
# Import the Score model from the Django app.
from ccnaquizbot.score.models import Score

# Function to update the user's score in the database.
@sync_to_async
def update_user_score(discord_id, username, points):
    """
    Update the user's score in the database.
    """
    print(f"Updating score for Discord ID: {discord_id}, Username: {username}, Points: {points}")  # Debug log
    score, created = Score.objects.get_or_create(discord_id=discord_id, defaults={'name': username, 'point': 0})
    score.point += points # Add points to the user's score.
    score.name = username  # Update username in case it changes
    score.save() # Save the updated score to the database.

def get_question(level):
    url = f"https://polar-forest-95759-e6c7774f6065.herokuapp.com/api/random/?level={level}"
    print(f"DEBUG - Attempting to call URL: {url}") # Debug log
    try:
        response = requests.get(url, timeout=5) # Make an HTTP GET request to the API.
        response.raise_for_status() # Raise an exception for HTTP errors.
        question_data = response.json() #Parse the JSON response.

        # Validate the API response.
        if not question_data or not isinstance(question_data, dict):
            print("DEBUG - Invalid API response: not a dictionary")
            return ("⚠️ Invalid API response.", None, None, None)

        # Format the question and extract the correct answer and explanation.
        qs = f"📘 **Question:**\n{question_data['title']}\n\n"
        answer = None
        correct_explanation = None
        for idx, item in enumerate(question_data['answers'], start=1):
            qs += f"{idx}. {item['answer']}\n"
            if item.get('is_correct'):
                answer = idx
                correct_explanation = item.get('explanation', 'No explanation provided.')

        # Handle cases where no correct answer is found.
        if answer is None:
            print("DEBUG - No correct answer found")
            return ("⚠️ No correct answer found.", None, None, None)

        # Include points and image URL if available.
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

# Initialize bot with commands and disable the default help command
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)


# Motivational messages
MOTIVATIONAL_MESSAGES = [
    "🌟 Keep pushing forward! Every small step counts toward success.",
    "📘 Remember: Consistency is key. Study a little every day!",
    "💡 'The beautiful thing about learning is that no one can take it away from you.' – B.B. King",
    "🚀 Believe in yourself! You’re capable of amazing things.",
    "📚 'Success is the sum of small efforts, repeated day in and day out.' – Robert Collier",
]
# Load channel IDs from .env
REMINDERS_STUDY_GROUP_CHANNEL_ID = int(os.getenv("REMINDERS_STUDY_GROUP_CHANNEL_ID"))

# Study reminders
STUDY_REMINDERS = [
    "🔔 Don’t forget to review your weak topics today!",
    "📖 Have you completed your practice tests for the day?",
    "📝 Make sure to revise your notes and flashcards!",
    "💻 Spend some time practicing subnetting or troubleshooting today.",
    "📘 Join your study group and discuss challenging topics together!",
]

# Task to send motivational messages and reminders
@tasks.loop(hours=6)  # Adjust the interval as needed
async def send_motivational_messages():
    channel = bot.get_channel(REMINDERS_STUDY_GROUP_CHANNEL_ID)
    if not channel:
        print(f"ERROR: Could not find channel with ID {REMINDERS_STUDY_GROUP_CHANNEL_ID}")
        return
    print(f"DEBUG - Found channel: {channel.name}")
    """
    Sends motivational messages and study reminders to the reminders_study_group channel.
    """
    channel = bot.get_channel(REMINDERS_STUDY_GROUP_CHANNEL_ID)
    if not channel:
        print(f"ERROR: Could not find channel with ID {"REMINDERS_STUDY_GROUP_CHANNEL_ID"}")
        return

    # Send a random motivational message
    motivational_message = random.choice(MOTIVATIONAL_MESSAGES)
    await channel.send(motivational_message)

    # Send a random study reminder
    study_reminder = random.choice(STUDY_REMINDERS)
    await channel.send(study_reminder)

# Assign students to study groups based on weak topics
@bot.command(name='assign_groups')
async def assign_study_groups(ctx):
    """
    Assigns students to study groups based on weak topics.
    """
    # Example data structure for tracking weak topics
    student_performance = {
        "Student1": ["Subnetting", "Routing"],
        "Student2": ["Switching", "Security"],
        "Student3": ["Routing", "Security"],
        "Student4": ["Subnetting", "Switching"],
    }

    # Group students by weak topics
    study_groups = {}
    for student, weak_topics in student_performance.items():
        for topic in weak_topics:
            if topic not in study_groups:
                study_groups[topic] = []
            study_groups[topic].append(student)

    # Send the study group assignments to the channel
    channel = bot.get_channel(REMINDERS_STUDY_GROUP_CHANNEL_ID)
    if not channel:
        print(f"ERROR: Could not find channel with ID {REMINDERS_STUDY_GROUP_CHANNEL_ID}")
        return

    await channel.send("📋 **Study Group Assignments Based on Weak Topics:**")
    for topic, students in study_groups.items():
        await channel.send(f"**{topic}:** {', '.join(students)}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not post_daily_quiz.is_running():
        print("DEBUG - Starting post_daily_quiz task")
        post_daily_quiz.start()
    else:
        print("DEBUG - post_daily_quiz task is already running")

    if not study_sessions.is_running():
        print("DEBUG - Starting study_sessions task")
        study_sessions.start()
    else:
        print("DEBUG - study_sessions task is already running")

    if not send_motivational_messages.is_running():
        print("DEBUG - Starting send_motivational_messages task")
        send_motivational_messages.start()
    else:
        print("DEBUG - send_motivational_messages task is already running")

@bot.command(name='quiz')
async def private_quiz(ctx, mode: str = None, level: int = None):
    """
    Allows students to take quizzes privately via DM.
    Usage: $quiz dm <level>
    """
    if mode != "dm":
        await ctx.send("⚠️ Invalid mode. Use `$quiz dm <level>` to take the quiz privately.")
        return

    if level not in [1, 2, 3]:
        await ctx.send("⚠️ Invalid level. Please specify level 1, 2, or 3. Example: `$quiz dm 2`")
        return

    # Send a DM to the user
    try:
        await ctx.author.send("📘 **Welcome to the Private Quiz!**\nYou will receive questions here. Answer them within 1 minute.")
    except discord.Forbidden:
        await ctx.send("⚠️ I cannot send you a DM. Please enable DMs from server members and try again.")
        return

    score = 0
    incorrect_questions = []

    # Fetch 5 questions for the specified level
    for _ in range(5):  # Limit to 5 questions
        qs, answer, explanation, image_url = get_question(level)

        # Send the question as an embed
        embed = discord.Embed(
            title="📘 Network Question",
            description=qs,
            color=discord.Color.blue()
        )
        if image_url and isinstance(image_url, str) and image_url.lower().startswith(('http://', 'https://')):
            embed.set_image(url=image_url)

        await ctx.author.send(embed=embed)

        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel) and m.content.isdigit()

        try:
            # Wait for the user's response (1 minute timeout)
            user_response = await bot.wait_for('message', check=check, timeout=60.0)

            if int(user_response.content) == answer:
                await ctx.author.send("✅ Correct!")
                score += 1
            else:
                await ctx.author.send(f"❌ Incorrect! The correct answer was: **{answer}**\n📝 **Explanation:** {explanation}")
                incorrect_questions.append(qs)

        except asyncio.TimeoutError:
            await ctx.author.send(f"⏰ Time's up! The correct answer was: **{answer}**\n📝 **Explanation:** {explanation}")
            incorrect_questions.append(qs)

    # Provide the final score and areas of improvement
    await ctx.author.send(f"**Quiz Complete!**\nYour score: {score}/5")
    if incorrect_questions:
        await ctx.author.send("**Areas of Improvement:**")
        for q in incorrect_questions:
            await ctx.author.send(f"🔸 {q}")
    else:
        await ctx.author.send("🎉 Great job! You answered all questions correctly!")

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

@bot.command(name='test')
async def simulated_ccna_test(ctx, level: int = None):
    """
    Simulates a CCNA test with 5 questions from the specified level.
    Tracks performance and suggests improvement areas.
    """
    if level not in [1, 2, 3]:
        await ctx.send("⚠️ Invalid level. Please specify level 1, 2, or 3. Example: `$test 2`")
        return

    # Fetch the channel where the test is being conducted
    test_channel = discord.utils.get(ctx.guild.channels, name="simulated_ccna_tests")
    if ctx.channel != test_channel:
        await ctx.send(f"⚠️ Please use this command in the `{test_channel.name}` channel.")
        return

    # Fetch 5 questions for the specified level
    flashcards = {
        1: [
            {"question": "Which two traffic types use the Real-Time Transport Protocol (RTP)?", "answer": "Video, Voice"},
            {"question": "Which wireless technology has low-power and data rate requirements, making it popular in home automation?", "answer": "ZigBee"},
            {"question": "Which layer of the TCP/IP model provides a route to forward messages through an internetwork?", "answer": "Internet"},
            {"question": "Which type of server relies on record types such as A, NS, AAAA, and MX?", "answer": "DNS"},
            {"question": "What are proprietary protocols?", "answer": "Protocols developed by organizations who have control over their definition and operation."},
        ],
        2: [
            {"question": "What does the IPv6 route ::/0 represent?", "answer": "It is the default route used when no specific match is found in the routing table."},
            {"question": "How do you configure a floating static route?", "answer": "Use a higher administrative distance than the dynamic protocol in use."},
            {"question": "What is the correct default IPv4 static route command?", "answer": "ip route 0.0.0.0 0.0.0.0 S0/0/0"},
            {"question": "What is VLAN hopping?", "answer": "An attack that exploits switch trunking to access VLANs without authorization."},
            {"question": "What type of attack does the 'macof' tool simulate?", "answer": "MAC address table overflow attack."},
        ],
        3: [
            {"question": "Which design feature limits the size of a failure domain in an enterprise network?", "answer": "The use of the building switch block approach"},
            {"question": "What must a network administrator modify on a router for password recovery?", "answer": "The configuration register value, the startup configuration file"},
            {"question": "What type of network uses one common infrastructure for voice, data, and video?", "answer": "Converged"},
            {"question": "What are three advantages of using private IP addresses and NAT?", "answer": "Hides private LAN addressing, permits LAN expansion, conserves public IP addresses"},
            {"question": "Which scenarios are examples of remote access VPNs?", "answer": "A mobile sales agent connecting via a hotel’s Internet, an employee using VPN client software from home"},
        ],
    }

    selected_questions = flashcards[level][:5]  # Select the first 5 questions
    score = 0
    incorrect_questions = []

    for idx, question in enumerate(selected_questions, start=1):
        # Send the question
        await ctx.send(f"**Question {idx}:** {question['question']}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Wait for the user's answer (1 minute timeout)
            user_response = await bot.wait_for('message', check=check, timeout=60.0)
            if user_response.content.strip().lower() == question['answer'].lower():
                await ctx.send("✅ Correct!")
                score += 1
            else:
                await ctx.send(f"❌ Incorrect! The correct answer was: **{question['answer']}**")
                incorrect_questions.append(question['question'])
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! The correct answer was: **{question['answer']}**")
            incorrect_questions.append(question['question'])

    # Provide the final score and areas of improvement
    await ctx.send(f"**Test Complete!**\nYour score: {score}/5")
    if incorrect_questions:
        await ctx.send("**Areas of Improvement:**")
        for q in incorrect_questions:
            await ctx.send(f"🔸 {q}")
    else:
        await ctx.send("🎉 Great job! You answered all questions correctly!")

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

STUDY_SESSION_CHANNEL_ID = int(os.getenv("STUDY_SESSION_CHANNEL_ID"))

@tasks.loop(hours=4)  # Run this task every 4 hours (adjust as needed)
async def study_sessions():
    """
    Posts flashcards and starts a structured study session using the Pomodoro technique.
    Allows users to request flashcards for specific CCNA levels.
    Sends 10 flashcards per session and continues in the next session.
    """
    # Fetch the channel
    channel = bot.get_channel(STUDY_SESSION_CHANNEL_ID)
    if not channel:
        print(f"ERROR: Could not find channel with ID {STUDY_SESSION_CHANNEL_ID}")
        return
    print(f"DEBUG - Found channel: {channel.name}")

    # Prompt users to select a CCNA level
    await channel.send(
        "📚 **Study Session Starting Soon!**\n"
        "Please reply with the CCNA level (1, 2, or 3) to receive flashcards for that level."
    )

    # Wait for user input
    def check(m):
        return m.channel == channel and m.content in ["1", "2", "3"] and not m.author.bot

    try:
        msg = await bot.wait_for('message', check=check, timeout=300.0)  # Wait for 5 minutes
        level = int(msg.content)
        await channel.send(f"✅ Flashcards for CCNA Level {level} will be sent shortly!")

        # Flashcards for each level
       # Flashcards for each level
        flashcards = {
            1: [
                {"question": "Which two traffic types use the Real-Time Transport Protocol (RTP)?", "answer": "Video, Voice"},
                {"question": "Which wireless technology has low-power and data rate requirements, making it popular in home automation?", "answer": "ZigBee"},
                {"question": "Which layer of the TCP/IP model provides a route to forward messages through an internetwork?", "answer": "Internet"},
                {"question": "Which type of server relies on record types such as A, NS, AAAA, and MX?", "answer": "DNS"},
                {"question": "What are proprietary protocols?", "answer": "Protocols developed by organizations who have control over their definition and operation."},
                {"question": "What service is provided by DNS?", "answer": "Resolves domain names, such as cisco.com, into IP addresses."},
                {"question": "A client packet has a destination port number of 110. What service is the client requesting?", "answer": "POP3"},
                {"question": "What command can be used on a Windows PC to see the IP configuration?", "answer": "ipconfig"},
                {"question": "A wired laser printer is shared on a home network. What networking model is in use?", "answer": "Peer-to-peer (P2P)"},
                {"question": "What characteristic describes a virus?", "answer": "Malicious software or code running on an end device."},
                {"question": "What are the priorities from highest to lowest for QoS on a corporate network with web, financial transactions, and audio conference data?", "answer": "Audio conference, financial transactions, web page"},
                {"question": "Match the IPv6 addressing component: This network portion is assigned by the provider.", "answer": "Global routing prefix"},
                {"question": "If Host1 transfers a file to a server, what TCP/IP model layers are used?", "answer": "Application, transport, Internet, and network access layers"},
                {"question": "What is a characteristic of cut-through switching?", "answer": "Low latency, may forward runt frames"},
                {"question": "Which router interface should be used as the default gateway for host H1?", "answer": "R1: G0/0"},
                {"question": "What service is provided by Internet Messenger?", "answer": "An application that allows real-time chatting among remote users."},
                {"question": "Match the network with the correct IP address and prefix for Network A (128 hosts).", "answer": "192.168.0.128 /25"},
                {"question": "Which protocol builds the ARP table?", "answer": "ARP"},
                {"question": "Which two factors may interfere with Ethernet cabling causing signal distortion?", "answer": "EMI, RFI"},
                {"question": "How does a host obtain a destination MAC address if it’s not in the ARP cache?", "answer": "It sends an ARP request for the MAC address of the default gateway."},
                {"question": "A client packet has a destination port number of 53. What service is the client requesting?", "answer": "DNS"},
                {"question": "What is the smallest network mask for a LAN supporting 25 devices?", "answer": "255.255.255.224"},
                {"question": "What characteristic describes a Trojan horse?", "answer": "Malicious software or code running on an end device."},
                {"question": "What service is provided by HTTPS?", "answer": "Uses encryption to secure the exchange of text, graphic images, sound, and video on the web."},
                {"question": "How does a PC track data flow between multiple application sessions?", "answer": "The data flow is tracked based on the source port number used by each application."},
                {"question": "What is the smallest network mask for a LAN supporting 61 devices?", "answer": "255.255.255.192"},
                {"question": "What characteristic describes a DoS attack?", "answer": "An attack that slows or crashes a device or network service."},
                {"question": "What service is provided by SMTP?", "answer": "Allows clients to send email to a mail server and servers to send email to other servers."},
                {"question": "Which scenario describes a function of the transport layer?", "answer": "The transport layer ensures the correct web page is delivered to the correct browser window."},
                {"question": "What does the term 'attenuation' mean in data communication?", "answer": "Loss of signal strength as distance increases."},
                {"question": "Which two protocols operate at the top layer of the TCP/IP protocol suite?", "answer": "POP, DNS"},
                {"question": "Which component is addressed in the AAA network service framework for access rights?", "answer": "Authorization"},
                {"question": "What are three requirements defined by network communication protocols?", "answer": "Message size, message encoding, delivery options"},
                {"question": "Which two characteristics describe IP?", "answer": "Does not require a dedicated end-to-end connection, operates independently of the network media."},
                {"question": "What three network characteristics are described in a scenario with secure login, QoS for video, and ISP failover?", "answer": "Security, quality of service, fault tolerance"},
                {"question": "Which two causes of signal degradation are common with UTP cabling?", "answer": "Improper termination, low-quality cable or connectors"},
                {"question": "Which subnet includes 192.168.1.96 as a usable host address?", "answer": "192.168.1.64/26"},
                {"question": "What tool can diagnose a failure to ping a URL but not an IP address?", "answer": "nslookup"},
                {"question": "What is the consequence of configuring a router with the ipv6 unicast-routing command?", "answer": "The IPv6 enabled router interfaces begin sending ICMPv6 Router Advertisement messages."},
                {"question": "Which three OSI model layers map to the TCP/IP application layer?", "answer": "Application, presentation, session"}
            ],
            2: [
                {"question": "What does the IPv6 route ::/0 represent?", "answer": "It is the default route used when no specific match is found in the routing table."},
                {"question": "How do you configure a floating static route?", "answer": "Use a higher administrative distance than the dynamic protocol in use."},
                {"question": "What is the correct default IPv4 static route command?", "answer": "ip route 0.0.0.0 0.0.0.0 S0/0/0"},
                {"question": "What is VLAN hopping?", "answer": "An attack that exploits switch trunking to access VLANs without authorization."},
                {"question": "What type of attack does the 'macof' tool simulate?", "answer": "MAC address table overflow attack."},
                {"question": "Why might a DHCPv6 pool show 0 active clients in stateless mode?", "answer": "The DHCPv6 server does not track address assignments in stateless mode."},
                {"question": "What VLAN type carries untagged traffic?", "answer": "Native VLAN."},
                {"question": "What does STP do in a network?", "answer": "It disables redundant paths to prevent Layer 2 loops."},
                {"question": "Which encryption method is most secure for wireless networks?", "answer": "WPA2 with AES."},
                {"question": "How does a switch behave if the MAC address table is empty?", "answer": "It floods the frame out of all ports except the incoming port."},
                {"question": "What is the purpose of PortFast on a switch?", "answer": "It allows access ports to transition immediately to the forwarding state."},
                {"question": "What does BPDU Guard do?", "answer": "It disables a port if a BPDU is received, protecting STP topology."},
                {"question": "What is a routed port on a multilayer switch?", "answer": "A physical port configured to act as a Layer 3 interface."},
                {"question": "What is the administrative distance of OSPF?", "answer": "110"},
                {"question": "What does DHCP snooping do?", "answer": "It builds a trusted MAC-to-IP database to prevent rogue DHCP servers."},
                {"question": "What command shows MAC addresses learned by a switch?", "answer": "show mac address-table"},
                {"question": "What command enables inter-VLAN routing on a Layer 3 switch?", "answer": "ip routing"},
                {"question": "What is the IPv6 link-local address prefix?", "answer": "FE80::/10"},
                {"question": "Which DHCPv4 message confirms the lease is successful?", "answer": "DHCPACK"},
                {"question": "What happens when a switch receives a frame with a multicast destination MAC?", "answer": "It floods the frame to all ports except the incoming one."},
                {"question": "What is a method to launch a VLAN hopping attack?", "answer": "Introducing a rogue switch and enabling trunking."},
                {"question": "What is a secure configuration option for remote access to a network device?", "answer": "Configure SSH."},
                {"question": "What type of network device includes a switch, WLAN, and firewall features?", "answer": "Wireless router."},
                {"question": "What protocol or technology disables redundant paths to eliminate Layer 2 loops?", "answer": "STP."},
                {"question": "Why were VLANs 10 and 100 not removed after erasing startup-config and reloading?", "answer": "They are stored in vlan.dat in flash memory, which must be manually deleted."},
                {"question": "Which two VTP modes allow for the creation, modification, and deletion of VLANs on the local switch?", "answer": "Server, transparent."},
                {"question": "Which three steps should be taken before moving a Cisco switch to a new VTP management domain?", "answer": "Configure the switch with the name of the new management domain, select the correct VTP mode and version, reboot the switch."},
                {"question": "How are Rapid PVST+ link types determined on switch interfaces?", "answer": "Link types are determined automatically."},
                {"question": "Compared with dynamic routes, what are two advantages of using static routes on a router?", "answer": "They improve network security, use fewer router resources."},
                {"question": "What is the effect of entering the spanning-tree portfast configuration command on a switch?", "answer": "It enables portfast on a specific switch interface."},
                {"question": "Which command will start the process to bundle two physical interfaces to create an EtherChannel group via LACP?", "answer": "interface range GigabitEthernet 0/4 – 5."},
                {"question": "Which three PAgP channel establishment modes are available?", "answer": "Auto, desirable, on."},
                {"question": "How should a static route be changed to allow user traffic from the LAN to reach the Internet?", "answer": "Change the destination network and mask to 0.0.0.0 0.0.0.0."},
                {"question": "What two default wireless router settings can affect network security?", "answer": "The SSID is broadcast, a well-known administrator password is set."},
                {"question": "What is the common term given to SNMP log messages that are generated by network devices and sent to the SNMP server?", "answer": "Traps."},
                {"question": "Which tab on a Cisco 3500 series WLC allows configuration of a new VLAN interface for a WLAN?", "answer": "CONTROLLER."},
                {"question": "Why would an administrator change the default DHCP IPv4 addresses on an AP?", "answer": "To reduce outsiders intercepting data or accessing the wireless network by using a well-known address range."},
                {"question": "Which two functions are performed by a WLC when using split MAC?", "answer": "Frame queuing and packet prioritization, association and re-association of roaming clients."},
                {"question": "On what switch ports should BPDU guard be enabled to enhance STP stability?", "answer": "All PortFast-enabled ports."},
                {"question": "Why is DHCP snooping required when using the Dynamic ARP Inspection feature?", "answer": "It uses the MAC-address-to-IP-address binding database to validate an ARP packet."}
            ],
            3: [
                {"question": "Which design feature limits the size of a failure domain in an enterprise network?", "answer": "The use of the building switch block approach"},
                {"question": "What must a network administrator modify on a router for password recovery?", "answer": "The configuration register value, the startup configuration file"},
                {"question": "What type of network uses one common infrastructure for voice, data, and video?", "answer": "Converged"},
                {"question": "What are three advantages of using private IP addresses and NAT?", "answer": "Hides private LAN addressing, permits LAN expansion, conserves public IP addresses"},
                {"question": "Which scenarios are examples of remote access VPNs?", "answer": "A mobile sales agent connecting via a hotel’s Internet, an employee using VPN client software from home"},
                {"question": "What are three benefits of cloud computing?", "answer": "Streamlines IT operations, enables access to data anywhere, reduces onsite IT equipment needs"},
                {"question": "What is a characteristic of a single-area OSPF network?", "answer": "All routers are in the backbone area"},
                {"question": "What is a WAN?", "answer": "A network infrastructure providing access over a large geographic area"},
                {"question": "What technology supports a backup site for company server data?", "answer": "Data center"},
                {"question": "Which OSPF packet is used to discover and establish neighbor adjacency?", "answer": "Hello"},
                {"question": "What are two characteristics of a virus?", "answer": "Can be dormant and activate later, typically requires end-user activation"},
                {"question": "Which public WAN technology uses copper telephone lines for multiplexed T3 connections?", "answer": "DSL"},
                {"question": "Which WAN connection provides high-speed, dedicated bandwidth for metropolitan areas?", "answer": "Ethernet WAN"},
                {"question": "Why would a penetration test team use debuggers?", "answer": "To reverse engineer binary files for exploits and malware analysis"},
                {"question": "What can be determined from an ACL applied with access-class in?", "answer": "Two devices with 192.168.10.x IP addresses used SSH or Telnet to access the router"},
                {"question": "What command clears dynamic NAT or PAT entries before timeout?", "answer": "clear ip nat translation"},
                {"question": "What are two characteristics of video traffic?", "answer": "Latency should not exceed 400 ms, more resilient to loss than voice"},
                {"question": "Why might a client PC fail to access a web server with static NAT?", "answer": "Interface S0/0/0 should be the outside NAT interface"},
                {"question": "What feature must be enabled for dynamic private IP address assignment to access the Internet?", "answer": "NAT"},
                {"question": "What trend allows multiple OS on a single CPU in a data center?", "answer": "Virtualization"},
                {"question": "Which address represents the inside global address in NAT?", "answer": "209.165.20.25"},
                {"question": "Which IPsec protocols provide data integrity?", "answer": "MD5, SHA"},
                {"question": "How does a host without Cisco AnyConnect gain access to the client image?", "answer": "Initiates a clientless VPN connection via a web browser to download the client"},
                {"question": "Which WAN options are private WAN architectures?", "answer": "Leased line, Ethernet WAN"},
                {"question": "Which QoS marking is applied to Ethernet frames?", "answer": "CoS"},
                {"question": "What can be obtained from the show ntp associations detail command?", "answer": "Router R1 is the master, the IP address of R1 is 192.168.1.2"},
                {"question": "Which extended ACL filters FTP and web traffic to a server?", "answer": "access-list 105 permit tcp host 10.0.70.23 host 10.0.54.5 eq 20\naccess-list 105 permit tcp host 10.0.70.23 host 10.0.54.5 eq 21\naccess-list 105 permit tcp 10.0.0.0 0.255.255.255 host 10.0.54.5 eq www\naccess-list 105 deny ip any host 10.0.54.5\naccess-list 105 permit ip any any\nApplied: R2(config)# interface gi0/0\nR2(config-if)# ip access-group 105 in"},
                {"question": "Where should a standard ACL be applied to allow only R2 G0/0 devices to access R1 G0/1?", "answer": "Outbound on the R1 G0/1 interface"},
                {"question": "What is a characteristic of a Type 2 hypervisor?", "answer": "Does not require management console software"},
                {"question": "What are the two types of VPN connections?", "answer": "Site-to-site, remote access"},
                {"question": "What conclusions can be drawn from an OSPF multiaccess network output?", "answer": "The DR can be reached through GigabitEthernet 0/0, this interface uses the default priority, the router ID values were not used to select DR and BDR"},
                {"question": "Why does an ACL deny Telnet connections to R1 vty lines?", "answer": "The IT group network is included in the deny statement"},
                {"question": "What does mGRE provide to DMVPN technology?", "answer": "Allows dynamic tunnel creation through a permanent tunnel source at the hub"},
                {"question": "What pre-populates the adjacency table in Cisco CEF?", "answer": "The ARP table"},
                {"question": "What command displays NAT configuration parameters and pool address counts?", "answer": "show ip nat statistics"},
                {"question": "What is the purpose of establishing a network baseline?", "answer": "Creates a point of reference for future network evaluations"},
                {"question": "Match WAN device/service to description:", "answer": "CPE: Devices and wiring at enterprise edge connecting to carrier\nDCE: Devices providing interface to WAN cloud\nDTE: Customer devices passing data for WAN transmission\nLocal loop: Physical connection from customer to service provider POP"},
                {"question": "What is a characteristic of standard IPv4 ACLs?", "answer": "Filter traffic based on source IP addresses only"},
                {"question": "What is wrong with an R1 NAT configuration?", "answer": "NAT-POOL2 is not bound to ACL 1"},
                {"question": "How can an OSPF router advertise a default route?", "answer": "Use the default-information originate command on R0-A"}
            ]
        }

        # Get the selected flashcards
        selected_flashcards = flashcards[level]
        total_flashcards = len(selected_flashcards)
        flashcards_per_session = 10
        session_count = (total_flashcards + flashcards_per_session - 1) // flashcards_per_session  # Calculate total sessions

        # Loop through flashcards in chunks of 10
        for session in range(session_count):
            start_index = session * flashcards_per_session
            end_index = start_index + flashcards_per_session
            current_flashcards = selected_flashcards[start_index:end_index]

            # Send the current set of flashcards
            await channel.send(f"📚 **Flashcards for CCNA Level {level} (Set {session + 1}/{session_count}):**")
            for idx, flashcard in enumerate(current_flashcards, start=1):
                # Generate the flashcard image
                image = create_flashcard_image(
                    question=flashcard["question"],
                    answer=flashcard["answer"],
                    card_number=start_index + idx
                )

                # Send the image to the channel
                with io.BytesIO() as image_binary:
                    image.save(image_binary, "PNG")
                    image_binary.seek(0)
                    await channel.send(file=discord.File(fp=image_binary, filename=f"flashcard_{start_index + idx}.png"))

                await asyncio.sleep(2)  # Add a short delay between flashcards

            # Start the study session
            await channel.send("⏳ **Study Session Starting!** Focus for the next 25 minutes.")
            await asyncio.sleep(25 * 60)  # 25 minutes of study time

            # Break time
            if session < session_count - 1:  # Only send break message if there are more flashcards
                await channel.send("⏰ **Break Time!** Relax for the next 5 minutes.")
                await asyncio.sleep(5 * 60)  # 5 minutes of break time

        # End of all sessions
        await channel.send("✅ **All Flashcards Complete! Great job, everyone!**")

    except asyncio.TimeoutError:
        await channel.send("⏰ No response received. Study session canceled.")

def create_flashcard_image(question, answer, card_number):
    """
    Creates an image for a flashcard with a white background.
    """
    # Image dimensions
    width, height = 800, 400
    background_color = "white"
    text_color = "black"

    # Create a blank image with a white background
    image = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(image)

    # Load a font (adjust the path to the font file as needed)
    try:
        font = ImageFont.truetype("arial.ttf", size=24)  # Use a system font
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font

    # Add the card number
    draw.text((10, 10), f"Flashcard {card_number}", fill=text_color, font=font)

    # Add the question
    draw.text((10, 50), f"Question:\n{question}", fill=text_color, font=font)

    # Add the answer
    draw.text((10, 200), f"Answer:\n{answer}", fill=text_color, font=font)

    return image
# Load the channel ID for resources_and_resources from .env
RESOURCES_CHANNEL_ID = int(os.getenv("RESOURCES_CHANNEL_ID"))

@bot.command(name='resources')
async def resources(ctx):
    """
    Provides links to official Cisco learning materials and YouTube tutorials.
    Usage: $resources
    """
    # Ensure the command is used in the correct channel
    if ctx.channel.id != RESOURCES_CHANNEL_ID:
        await ctx.send(f"⚠️ Please use this command in the `resources_and_resources` channel.")
        return

    # Send resources
    await ctx.send(
        "**📚 Official Cisco Learning Materials and Tutorials:**\n"
        "1. [Cisco Networking Academy](https://www.netacad.com/)\n"
        "2. [Cisco Certification Roadmap](https://learningnetwork.cisco.com/s/certification-roadmaps)\n"
        "3. [Cisco Packet Tracer](https://www.netacad.com/courses/packet-tracer)\n"
        "4. [Cisco YouTube Channel](https://www.youtube.com/user/cisconetworks)\n"
        "5. [NetworkChuck YouTube Channel](https://www.youtube.com/c/NetworkChuck)\n"
        "6. [David Bombal YouTube Channel](https://www.youtube.com/c/DavidBombal)\n"
        "7. [Free CCNA Study Guide](https://www.freeccnastudyguide.com/)\n"
    )


@bot.command(name='help')
async def help_command(ctx, topic: str = None):
    """
    Explains networking concepts and lists available bot commands.
    Usage: $help <topic>
    """
    # Ensure the command is used in the correct channel
    if ctx.channel.id != RESOURCES_CHANNEL_ID:
        await ctx.send(f"⚠️ Please use this command in the `resources_and_support` channel.")
        return

    # Predefined explanations for networking concepts
    explanations = {
        "subnetting": "Subnetting is the process of dividing a network into smaller, more manageable sub-networks. It helps improve network performance and security.",
        "osi": "The OSI model is a conceptual framework used to understand network interactions. It has 7 layers: Physical, Data Link, Network, Transport, Session, Presentation, and Application.",
        "tcp/ip": "The TCP/IP model is a simplified version of the OSI model with 4 layers: Application, Transport, Internet, and Network Access.",
        "nat": "NAT (Network Address Translation) is a method used to map private IP addresses to a public IP address to enable devices on a private network to access the internet.",
        "dns": "DNS (Domain Name System) translates human-readable domain names (e.g., google.com) into IP addresses that computers use to identify each other on the network.",
    }

    if topic is None:
        # List of available commands
        commands_list = (
            "**🛠️ Available Commands:**\n"
            "1. `$resources` - Provides links to official Cisco learning materials and YouTube tutorials.\n"
            "2. `$help <topic>` - Explains networking concepts. Use `$help` to see available topics.\n"
            "3. `$quiz dm <level>` - Take a private quiz via DM. Specify the level (1, 2, or 3).\n"
            "4. `$ccna <level>` - Answer a CCNA question in the current channel. Specify the level (1, 2, or 3).\n"
            "5. `$test <level>` - Simulate a CCNA test with 5 questions. Specify the level (1, 2, or 3).\n"
            "6. `$leaderboard` - View the leaderboard of top scorers.\n"
            "7. `$assign_groups` - Assign students to study groups based on weak topics.\n"
        )

        # Networking topics
        topics_list = (
            "**📝 Available Topics for `$help <topic>`:**\n"
            "1. `subnetting`\n"
            "2. `osi`\n"
            "3. `tcp/ip`\n"
            "4. `nat`\n"
            "5. `dns`\n"
            "Use `$help <topic>` to learn more about a specific topic. Example: `$help subnetting`"
        )

        await ctx.send(f"{commands_list}\n\n{topics_list}")
    else:
        # Provide explanation for the requested topic
        explanation = explanations.get(topic.lower())
        if explanation:
            await ctx.send(f"**📘 {topic.capitalize()} Explanation:**\n{explanation}")
        else:
            await ctx.send(f"⚠️ Sorry, I don't have an explanation for `{topic}`. Use `$help` to see available topics.")

# Use the token from the .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(os.getenv('DISCORD_TOKEN'))