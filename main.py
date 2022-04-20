from dotenv import load_dotenv
from os import getenv
import inflect
import random

load_dotenv()
from asyncio.exceptions import TimeoutError
import discord
from discord import Option
import sqlite3

intents = discord.Intents.all()
client = discord.Bot(intents=intents)
db = sqlite3.connect('database.db')
cursor = db.cursor()
engine = inflect.engine()

guild_ids=[961105485325533224]

def insert_user(user_id):
	with db:
		cursor.execute(f"INSERT INTO coins VALUES ({user_id}, 1000)")

def get_user(user_id):
	cursor.execute(f"SELECT * FROM coins WHERE user_id={user_id}")
	return cursor.fetchall()

def update_coin(user_id, amount):
	with db:
		cursor.execute(f"""UPDATE coins SET coins = {amount} WHERE user_id = {user_id}""")

@client.slash_command(guild_ids=guild_ids)
async def balance(ctx, user: discord.Member = None):
	user = user or ctx.author
	fetch = get_user(int(user.id))
	print(fetch, user.id)

	if len(fetch) <= 0:
		insert_user(int(user.id))
		await ctx.respond(f"{user.mention} has 1000 coins.")
	else:
		await ctx.respond(f"{user.mention} has {fetch[0][1]} coins.")

	db.commit()

@client.slash_command(guild_ids=guild_ids)
async def coinflip(ctx, amount: int = None):
	if amount is None: return await ctx.respond("Please specify an amount.")
	if get_user(int(ctx.author.id))[0] is None: insert_user(int(ctx.author.id))
	if amount < 0: return await ctx.respond("Please specify a positive amount.")
	if amount > get_user(int(ctx.author.id))[0][1]: return await ctx.respond(f"You are missing **{amount - get_user(int(ctx.author.id))[0][1]}** coins!")

	amount = amount * random.randint(-1, 1)
	print(amount)

	if amount > 0:
		await ctx.respond(f"{ctx.author.mention} flipped head and won **{amount}** coins!")
	elif amount < 0:
		await ctx.respond(f"{ctx.author.mention} flipped tails and lost **{abs(amount)}** coins!")
	else:
		await ctx.respond(f"{ctx.author.mention} landed the coin on the side?!")

	update_coin(int(ctx.author.id), get_user(int(ctx.author.id))[0][1] + amount)

	db.commit()

@client.slash_command(guild_ids=guild_ids)
async def pay(ctx, user: discord.Member = None, amount: int = None):
	if user is None: return await ctx.respond("Please specify a user.")
	if amount is None: return await ctx.respond("Please specify an amount.")
	if amount < 0: return await ctx.respond("Please specify a positive amount.")
	if amount > get_user(int(ctx.author.id))[0][1]: return await ctx.respond(f"You are missing **{amount - get_user(int(ctx.author.id))[0][1]}** coins!")

	update_coin(int(ctx.author.id), get_user(int(ctx.author.id))[0][1] - amount)
	update_coin(int(user.id), get_user(int(user.id))[0][1] + amount)
	db.commit()
	await ctx.respond(f"{ctx.author.mention} has paid {user.mention} **{amount}** coins!")

def check_answer(author, attempt, answer):
	def inner_check(message): 
		if message.author != author:
			return False
		try:
			if int(attempt) == answer:
				return True 
			return False
		except ValueError: 
			return False
	return inner_check

def generate_random_math_equation(difficulty):
	number = "123456789"
	operations = "+-/*"
	operator = []
	original = []

	for i in range(difficulty):
		operator.append(f"{int(random.choice(number)) * int(random.choice(number))} {random.choice(operations)}")
	operator.append(f"{int(random.choice(number)) * int(random.choice(number))}")

	for i in ' '.join(operator).split(" "):
		if i not in operations:
			i = engine.number_to_words(i)

		original.append(i)

	return (
		' '.join(operator),
		round(eval(''.join(operator)), 2),
		' '.join(original)
	)

@client.slash_command(guild_ids=guild_ids)
async def quiz(ctx):
	await ctx.respond(f"Welcome to the Quizshow!\n\nWhat shall your difficulty be today?\n1. Easy\n2. Medium\n3. Hard\n\nInput your choice by saying the number!")
	try:
		msg = await client.wait_for("message", check=lambda message: message.author == ctx.author, timeout=15)
		if msg:
			readable_difficulty = "easy"
			if msg.content == "2":
				readable_difficulty = "medium"
			elif msg.content == "3":
				readable_difficulty = "hard"
			if int(msg.content) in [1, 2, 3]:
				eq = generate_random_math_equation(int(msg.content) * 2)
				await ctx.send(f"You've selected difficulty **{readable_difficulty}**.\n\nThe question is: ```\n{eq[2]}\n```\nThe answers will be rounded to the second decimal, input your answer in the chatbox! There is only one attempt!")
				try:
					answer = await client.wait_for("message", check=lambda message: message.author == ctx.author, timeout=15)
					if round(float(answer.content), 2) == eq[1]:
						await ctx.send(f"Correct!\n\nThe answer was: {eq[1]}!\n\nGood job {ctx.author.mention}! You win **{500 * int(msg.content)}**$! :gigachad:")
						update_coin(int(ctx.author.id), get_user(int(ctx.author.id))[0][1] + 500 * int(msg.content))
					else:
						await ctx.send(f"Incorrect!\n\nThe answer was: {eq[1]}!\nYou lose! :sob:\nTry again next time!")
				except TimeoutError:
					await ctx.send(f"You ran out of time! :skull: The correct answer was: ```\n{eq[2]}\n```\nTry again next time..")
			else:
				await ctx.send("Unfortunately, that is not a valid difficulty! Try again by doing /quiz!")

	except TimeoutError:
		await ctx.send("You ran out of time to choose the difficulty!")

# Events
@client.event
async def on_member_join(member):
	cursor.execute(f"INSERT INTO coins VALUES ({int(member.id)}, 1000)")

@client.event
async def on_ready():
	cursor.execute("""CREATE TABLE IF NOT EXISTS coins (
		user_id INTEGER,
		coins INTEGER
	)""")
	db.commit()
	print("Ready to fly this plane!")

# db.close()
client.run(getenv("DISCORD_TOKEN"))