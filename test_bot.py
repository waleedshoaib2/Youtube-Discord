#!/usr/bin/env python3
"""
Simple Discord Bot Connection Test
"""

import discord
from discord import app_commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Bot is online!")
        print(f"🤖 Logged in as: {self.user} (ID: {self.user.id})")
        print(f"📊 Connected to {len(self.guilds)} servers")
        
        # List all servers
        for guild in self.guilds:
            print(f"  • {guild.name} (ID: {guild.id})")
            
        print("\n🔍 Testing slash commands...")
        try:
            await self.tree.sync()
            print("✅ Slash commands synced successfully!")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")

# Create bot instance
client = TestBot()

@client.tree.command(name="test", description="Test command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Bot is working!")

@client.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latency: {round(client.latency * 1000)}ms")

if __name__ == "__main__":
    # Get bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found in .env file!")
        print("Please add: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)
    
    print("🚀 Starting Discord bot test...")
    print(f"🔑 Token found: {token[:10]}...{token[-10:]}")
    
    try:
        client.run(token)
    except discord.LoginFailure:
        print("❌ Invalid bot token! Please check your DISCORD_BOT_TOKEN")
    except Exception as e:
        print(f"❌ Error connecting: {e}") 