# import discord
# from discord.ext import commands
# import json

# with open("token.json", "r", encoding="utf-8") as f:
#     token = json.load(f)

# TOKEN = token["xorgamebot"]

# games = {}

# intents = discord.Intents.default()
# intents.message_content = True

# bot = commands.Bot(command_prefix="!", intents=intents)

# tree = bot.tree

# @bot.command(name="xor")
# async def xor_command(ctx,command: str, *data):
#     # 현재 thread id
#     thread_id = ctx.channel.id
    
#     if command == "시작":
        
#         if thread_id in games:
#             await ctx.send("이미 게임이 진행중인 게시물입니다.")
#             return
        
#         if len(data) < 1:
#             await ctx.send("시작 값을 입력하세요")
#             return
        
#         try:
#             v = int(data[0])
#         except:
#             await ctx.send("숫자를 입력하세요")
#             return
        
#         games[thread_id] = {
#             "k": 2,
#             "n": v,
#             "dead": set(),
#             "last_value": v,
#             "last_user": None
#         }

#         await ctx.send("xor게임 시작!")
#         await ctx.send("시작 : " + str(v))

#     elif command == "종료":
#         if thread_id in games:
#             await ctx.send("xor게임 종료")
#             del games[thread_id]

#     elif command == "설명":
#         await ctx.send("첫 사람이 임의의 자연수 n을 말하면, k째사람이 n xor (k-1)을 말하는 게임")

# @bot.event
# async def on_message(message):

#     if message.author.bot:
#         return

#     if message.content.startswith("!"):
#         await bot.process_commands(message)
#         return

#     thread_id = message.channel.id
#     if thread_id not in games:
#         return
    
#     game = games[thread_id]
    
#     if message.author.id in game["dead"] or message.author.id == game["last_user"]:
#         await message.delete()
#         return

#     try:
#         value = int(message.content)
#     except:
#         await message.channel.send("숫자를 입력해주세요")
#         return

#     if value == game["last_value"]:
#         game["dead"].add(message.author.id)
#         await message.delete()
#         return
    
#     expected = game["n"] ^ (game["k"] - 1)

#     if value != expected:
#         await message.channel.send("실패! 입력해야 했던 값 : " + str(expected))
#         game["dead"].add(message.author.id)
#         return
    
#     game["last_value"] = value
#     game["last_user"] = message.author.id
#     game["k"] += 1

# bot.run(TOKEN)


import discord
from discord.ext import commands
import json

with open("token.json", "r", encoding="utf-8") as f:
    token = json.load(f)

TOKEN = token["xorgamebot"]

games = {}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print("봇 실행 완료")


@tree.command(name="xor_start", description="xor 게임 시작")
async def xor_start(interaction: discord.Interaction, n: int):

    thread_id = interaction.channel.id

    if thread_id in games:
        await interaction.response.send_message(
            "이미 게임이 진행중인 게시물입니다."
        )
        return

    games[thread_id] = {
        "k": 2,
        "n": n,
        "dead": set(),
        "last_value": n,
        "last_user": None
    }

    await interaction.response.send_message(
        f"xor게임 시작!\n시작 : {n}"
    )


@tree.command(name="xor_end", description="xor 게임 종료")
async def xor_end(interaction: discord.Interaction):

    thread_id = interaction.channel.id

    if thread_id in games:
        del games[thread_id]
        await interaction.response.send_message("xor게임 종료")
    else:
        await interaction.response.send_message("진행중인 게임이 없습니다.")


@tree.command(name="xor_help", description="xor 게임 설명")
async def xor_help(interaction: discord.Interaction):

    await interaction.response.send_message(
        "첫 사람이 임의의 자연수 n을 말하면, "
        "k째사람이 n xor (k-1)을 말하는 게임"
    )


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    thread_id = message.channel.id

    if thread_id not in games:
        return

    game = games[thread_id]

    if (
        message.author.id in game["dead"]
        or message.author.id == game["last_user"]
    ):
        await message.delete()
        return

    try:
        value = int(message.content)
    except:
        await message.channel.send("숫자를 입력해주세요")
        return

    if value == game["last_value"]:
        game["dead"].add(message.author.id)
        await message.delete()
        return

    expected = game["n"] ^ (game["k"] - 1)

    if value != expected:
        await message.channel.send(
            f"실패! 입력해야 했던 값 : {expected}"
        )

        game["dead"].add(message.author.id)
        return

    game["last_value"] = value
    game["last_user"] = message.author.id
    game["k"] += 1


bot.run(TOKEN)