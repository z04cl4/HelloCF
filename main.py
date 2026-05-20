import discord
import requests
import time
import json
import os

from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()

url = "https://codeforces.com/api/contest.list"

TOKEN = os.getenv("token")

try:
	with open("config.json", "r", encoding="utf-8") as f:
		configs = json.load(f)
except FileNotFoundError:
    configs = {}

intents = discord.Intents.default()

bot = commands.Bot(command_prefix = "!", intents = intents)

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}")

	try:
		synced = await bot.tree.sync()
		print(f"Synced {len(synced)} commands")

	except Exception as e:
		print(e)

	if not checker.is_running():
		checker.start()

@bot.tree.command(name = "cf", description="Show upcoming contests")
async def cf(interaction: discord.Interaction):
	data = requests.get(url).json()

	contests = []

	for contest in data["result"]:

		if contest["phase"] == "BEFORE":
			contests.append(contest)

	embed = discord.Embed(
		title="📅 Upcoming Codeforces Contests",
		color=0x5865F2
	)

	contests.reverse()

	for contest in contests[:5]:

		ts = contest["startTimeSeconds"]

		dt = datetime.fromtimestamp(ts, tz = ZoneInfo("Asia/Taipei")) # transform time

		tstr = dt.strftime("%Y-%m-%d %H:%M") 

		embed.add_field(
			name = contest["name"],
			value = (f"{tstr}\n"f"<t:{ts}:R>"),
			inline = False
		)

	await interaction.response.send_message(
		embed=embed
	)

@bot.tree.command(
	name="init_setting",
	description="Set reminder channel and role"
)
async def init_setting(
	interaction: discord.Interaction,
	channel: discord.TextChannel,
	role: discord.Role
):

	guild_id = str(interaction.guild.id)

	configs[guild_id] = {
		"channel": channel.id,
		"role": role.id
	}

	# save json
	with open("config.json", "w", encoding="utf-8") as f:
		json.dump(configs, f, indent = 4)

	await interaction.response.send_message(
		"Setup complete!"
	)

remained = set()

@tasks.loop(minutes = 1)
async def checker():

	data = requests.get(url).json()

	now = int(time.time())

	for c in data["result"]:

		if c["phase"] != "BEFORE":
			continue

		ts = c["startTimeSeconds"]

		diff = ts - now

		if 0 < diff <= 1800:

			if c["id"] in remained:
				continue

			remained.add(c["id"])

			# send to every guild
			for guild_id, cfg in configs.items():

				channel = bot.get_channel(
					cfg["channel"]
				)

				if channel is None:
					continue

				role = channel.guild.get_role(
					cfg["role"]
				)

				if role is None:
					continue

				await channel.send(
					f"{role.mention} 🔔 "
					f"**{c['name']}** starts "
					f"<t:{ts}:R>!"
				)

bot.run(TOKEN)