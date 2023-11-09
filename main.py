import nextcord
import config
import os
from nextcord.ext import commands

# Create Bot
intents = nextcord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=config.TOKEN, intents=intents)

# Create First Event
@bot.event
async def on_ready():
    print(f'{bot.user.name} is live!')

# Load Cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}') 

# Run the bot
bot.run(config.TOKEN)