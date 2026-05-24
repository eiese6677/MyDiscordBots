import discord
import json
import os
from datetime import datetime, timedelta, timezone

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

import json

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_ID = config["application_id"]["rankingbot"]
TOKEN = config["token"]["rankingbot"]

# =========================
# 한글 폰트 설정 (라즈베리파이)
# =========================
font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
font_prop = fm.FontProperties(fname=font_path)

plt.rcParams['axes.unicode_minus'] = False

# =========================
# 디스코드 설정
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

# =========================
# 설정
# =========================
DATA_FILE = "data.json"

RANK_MESSAGE_ID = 1499380228093382937
RANK_CHANNEL_NAME = "랭킹"

# =========================
# 그래프 생성
# =========================
def make_ranking_graph(counts, guild):
    users = []
    values = []

    sorted_data = sorted(
        counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for uid, count in sorted_data[:30]:

        member = guild.get_member(int(uid))

        if member is None:
            continue

        users.append(member.display_name)
        values.append(count)

    plt.figure(figsize=(10, 5))

    plt.bar(users, values)

    plt.xticks(
        rotation=45,
        ha='right',
        fontproperties=font_prop
    )

    plt.yticks(fontproperties=font_prop)

    plt.tight_layout()

    path = "ranking_graph.png"

    plt.savefig(path)
    plt.close()

    return path

# =========================
# 데이터 로드
# =========================
def load_data():

    if os.path.exists(DATA_FILE):

        with open(DATA_FILE, "r") as f:
            return json.load(f)

    return {}

# =========================
# 데이터 저장
# =========================
def save_data():

    with open(DATA_FILE, "w") as f:
        json.dump(counts, f)

counts = load_data()

# =========================
# 유저 이름 가져오기
# =========================
async def get_member_or_user(guild, uid):

    member = guild.get_member(int(uid))

    if member is not None:
        return member

    try:
        user = await client.fetch_user(int(uid))
        return user
    except:
        return None

# =========================
# 랭킹 문자열 생성
# =========================
async def build_ranking_text(guild):

    result = "# 메시지 랭킹\n\n"

    rank = 1

    sorted_data = sorted(
        counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for uid, count in sorted_data:

        member = await get_member_or_user(guild, uid)

        if member is None:
            continue

        name = getattr(member, "display_name", member.name)

        result += f"{rank}. {name} - {count}개\n"

        rank += 1

    return result

# =========================
# 봇 시작
# =========================
@client.event
async def on_ready():

    print(f"로그인 완료: {client.user}")

# =========================
# 메시지 이벤트
# =========================
@client.event
async def on_message(message):

    global counts

    if message.author.bot:
        return

    # =========================
    # 실시간 카운트
    # =========================
    uid = str(message.author.id)

    counts[uid] = counts.get(uid, 0) + 1

    if counts[uid] % 5 == 0:
        save_data()

    # =========================
    # 명령어 체크
    # =========================
    if not message.content.startswith("!랭킹"):
        return

    parts = message.content.split()

    # =========================
    # help
    # =========================
    if len(parts) >= 2 and parts[1] == "help":

        help_text = (
            "# 랭킹 봇 명령어\n\n"

            "## 기본 기능\n"
            "!랭킹 → 현재 메시지 랭킹 표시\n"
            "!랭킹 그래프 → 그래프 출력\n"
            "!랭킹 초기화 → 저장된 데이터 삭제\n\n"

            "## 과거 메시지 스캔\n"
            "!랭킹 init [일수]\n"
            "예: !랭킹 init 7\n"
            "예: !랭킹 init -1\n\n"

            "## 채널 제외\n"
            "!랭킹 init [일수] 제외 [번호들]\n"
            "예: !랭킹 init 7 제외 2 3\n\n"

            "## 채널 목록\n"
            "!랭킹 채널\n"
        )

        await message.channel.send(help_text)

        return

    # =========================
    # 초기화
    # =========================
    if len(parts) >= 2 and parts[1] == "초기화":

        counts.clear()

        save_data()

        await message.channel.send("랭킹 초기화 완료")

        return

    # =========================
    # 채널 목록
    # =========================
    if len(parts) >= 2 and parts[1] == "채널":

        result = "# 채널 목록\n\n"

        for i, ch in enumerate(message.guild.text_channels, start=1):
            result += f"{i}. {ch.name}\n"

        await message.channel.send(result)

        return

    # =========================
    # 그래프
    # =========================
    if len(parts) >= 2 and parts[1] == "그래프":

        path = make_ranking_graph(
            counts,
            message.guild
        )

        await message.channel.send(
            file=discord.File(path)
        )

        return

    # =========================
    # init
    # =========================
    if len(parts) >= 2 and parts[1] == "init":

        days = 7

        if len(parts) >= 3:

            try:
                days = int(parts[2])
            except:
                pass

        guild = message.guild

        counts.clear()

        # 날짜 설정
        if days == -1:

            after = None

            await message.channel.send(
                "전체 메시지 스캔 시작"
            )

        else:

            after = (
                datetime.now(timezone.utc)
                - timedelta(days=days)
            )

            await message.channel.send(
                f"최근 {days}일 스캔 시작"
            )

        status_msg = await message.channel.send(
            "0% 시작..."
        )

        channels = guild.text_channels

        total_channels = len(channels)

        done = 0

        last_percent = -1

        # 제외 채널
        exclude_indexes = set()

        if "제외" in parts:

            idx = parts.index("제외")

            for x in parts[idx + 1:]:

                try:
                    exclude_indexes.add(int(x) - 1)
                except:
                    pass

        # 스캔
        for i, channel in enumerate(channels):

            if i in exclude_indexes:
                continue

            try:

                if after is None:
                    history = channel.history(limit=None)
                else:
                    history = channel.history(
                        limit=None,
                        after=after
                    )

                async for msg in history:

                    if msg.author.bot:
                        continue

                    uid = str(msg.author.id)

                    counts[uid] = (
                        counts.get(uid, 0) + 1
                    )

            except Exception as e:

                print(
                    f"{channel.name} 오류:",
                    e
                )

            done += 1

            percent = int(
                done / total_channels * 100
            )

            if percent != last_percent:

                await status_msg.edit(
                    content=(
                        f"{percent}% 완료 "
                        f"({channel.name})"
                    )
                )

                last_percent = percent

        save_data()

        result = await build_ranking_text(guild)

        await message.channel.send(result)

        await status_msg.edit(
            content="100% 완료!"
        )

        return

    # =========================
    # 기본 랭킹
    # =========================
    if len(parts) == 1:

        result = await build_ranking_text(
            message.guild
        )

        await message.channel.send(result)

        # 랭킹 채널 자동 업데이트
        rank_channel = discord.utils.get(
            message.guild.text_channels,
            name=RANK_CHANNEL_NAME
        )

        if rank_channel:

            try:

                msg = await rank_channel.fetch_message(
                    RANK_MESSAGE_ID
                )

                await msg.edit(content=result)

            except discord.NotFound:

                msg = await rank_channel.send(
                    result
                )

                print(
                    "새 메시지 ID:",
                    msg.id
                )

            except discord.Forbidden:

                print("권한 없음")

# =========================
# 실행
# =========================
client.run(TOKEN)