import discord
import requests 
import json
import asyncio

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the intent to read message content

# Create client with intents
client = discord.Client(intents=intents)

def get_question():
    qs = ''         # Initialize the question string
    id = 1          # Used to number the answer choices
    answer = 0      # Will hold the correct answer's number

    try:
        # Try sending a GET request to the Django API (local server)
        response = requests.get("http://127.0.0.1:8000/api/random/", timeout=5)
        
        # Raise an error if the response returned a bad HTTP status code
        response.raise_for_status()
        
        # Parse the response text as JSON
        json_data = response.json()

    except requests.exceptions.RequestException as e:
        # Catch all types of request errors: connection errors, timeouts, etc.
        print(f"Error contacting API: {e}")
        
        # Return a user-friendly message and None to indicate failure
        return ("⚠️ Could not reach the question server. Please try again later.", None)

    # Start building the question output
    qs += "📘 **Question:**\n"
    qs += json_data[0]['title'] + "\n\n"

    # Loop through the answer choices in the API response
    for item in json_data[0]['answer']:
        # Add each answer choice to the message, numbered
        qs += f"{id}. {item['answer']}\n"

        # If this answer is marked as correct, store its number
        if item['is_correct']:
            answer = id

        id += 1  # Increment the answer number

    # Return the full question string and the correct answer number
    return (qs, answer)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    # Prevent bot from responding to itself
    if message.author == client.user:
        return

    # Only respond to messages that start with "$question"
    if message.content.startswith('$question'):
        
        # Get question and correct answer
        qs, answer = get_question()
        
        # Send the question (or error message)
        await message.channel.send(qs)

        # If the API was down, answer will be None — so stop here
        if answer is None:
            return

        # Function to validate user's guess (must be a number from the same user)
        def check(m):
            return m.author == message.author and m.content.isdigit()

        try:
            # Wait for the user's guess (2 seconds max)
            guess = await client.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            # If user doesn't reply in time
            return await message.channel.send('Sorry, you took too long!')

        # Check if their guess was correct
        if int(guess.content) == answer:
            await message.channel.send('✅ You are right!')
        else:
            await message.channel.send('❌ Oops. That is not right.')

    
client.run('MTM1NzcyNzg3OTY0NzE5OTI2Mg.G7E9Xn.9_8NknW_BBEdX4M3lnFmcqylYjJ4L2ffVuAHS8')

