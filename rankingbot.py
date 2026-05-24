import discord

import json

import os

from datetime import datetime, timedelta, timezone

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

import matplotlib.font_manager as fm

with open("token.json", "r", encoding="utf-8") as f:
    token = json.load(f)

TOKEN = token["xorgamebot"]

# 폰트 설정

font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

font_prop = fm.FontProperties(fname=font_path)



intents = discord.Intents.default()

intents.message_content = True

intents.members = True  # 닉네임으로 멤버를 찾으려면 반드시 True여야 함



client = discord.Client(intents=intents)



DATA_FILE = "data.json"

GROUP_FILE = "groups.json"



is_init = False



# -------------------------

# 데이터 관리

# -------------------------

def load_all_data():

    u_counts = {}

    g_data = {}

    if os.path.exists(DATA_FILE):

        with open(DATA_FILE, "r") as f:

            u_counts = json.load(f)

    if os.path.exists(GROUP_FILE):

        with open(GROUP_FILE, "r") as f:

            raw_groups = json.load(f)

            g_data = {k: set(map(str, v)) for k, v in raw_groups.items()}

    return u_counts, g_data



def save_all_data():

    with open(DATA_FILE, "w") as f:

        json.dump(user_counts, f)

    with open(GROUP_FILE, "w") as f:

        json.dump({k: list(v) for k, v in groups.items()}, f)



user_counts, groups = load_all_data()



# -------------------------

# 그래프 함수

# -------------------------

def make_ranking_graph(u_counts, g_data, guild):

    combined = {}

    all_grouped_users = set().union(*g_data.values()) if g_data else set()



    for gname, members in g_data.items():

        combined[gname] = sum(int(u_counts.get(str(m), 0)) for m in members)

    for uid, cnt in u_counts.items():

        if str(uid) not in all_grouped_users:

            combined[uid] = cnt



    sorted_data = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:15]

    

    labels, values = [], []

    for name, count in sorted_data:

        if str(name).isdigit():

            member = guild.get_member(int(name))

            labels.append(member.display_name if member else str(name))

        else:

            labels.append(name)

        values.append(count)



    plt.figure(figsize=(8, 4))

    plt.bar(labels, values)

    plt.xticks(rotation=45, fontproperties=font_prop)

    plt.tight_layout()

    path = "ranking_graph.png"

    plt.savefig(path)

    plt.close()

    return path



@client.event

async def on_ready():

    print(f"로그인 완료: {client.user}")



@client.event

async def on_message(message):

    global user_counts, groups, is_init

    if message.author.bot: return



    uid = str(message.author.id)

    user_counts[uid] = user_counts.get(uid, 0) + 1

    if not is_init and user_counts[uid] % 10 == 0: save_all_data()



    if not message.content.startswith("!랭킹"): return

    parts = message.content.split()



    # [초기화]

    if len(parts) >= 2 and parts[1] == "초기화":

        user_counts.clear()

        save_all_data()

        await message.channel.send("✅ 모든 유저 데이터가 초기화되었습니다.")

        return



    # [그룹 생성] !랭킹 group [그룹명] [닉네임1] [닉네임2] ...

    if len(parts) >= 4 and parts[1] == "group":

        group_name = parts[2]

        member_names = parts[3:]

        found_ids = set()

        not_found = []



        for name in member_names:

            # 1. 멘션 처리 (<@!123...>)

            clean_id = ''.join(filter(str.isdigit, name))

            if clean_id and len(clean_id) >= 17:

                found_ids.add(clean_id)

                continue

            

            # 2. 닉네임/이름으로 멤버 검색

            member = discord.utils.find(lambda m: m.display_name == name or m.name == name, message.guild.members)

            if member:

                found_ids.add(str(member.id))

            else:

                not_found.append(name)



        groups[group_name] = found_ids

        save_all_data()



        msg = f"👥 그룹 **{group_name}** 설정 완료 (멤버 {len(found_ids)}명)"

        if not_found:

            msg += f"\n⚠️ 찾을 수 없는 사용자: {', '.join(not_found)}"

        await message.channel.send(msg)

        return



    # [재스캔] !랭킹 init [일수] 제외 [순서...]

    if len(parts) >= 2 and parts[1] == "init":

        is_init = True

        days = 7

        exclude_indices = set()

        

        if "제외" in parts:

            idx = parts.index("제외")

            for x in parts[idx+1:]:

                try: exclude_indices.add(int(x) - 1)

                except: pass

            if idx > 2:

                try: days = int(parts[2])

                except: pass

        elif len(parts) >= 3:

            try: days = int(parts[2])

            except: pass



        user_counts.clear()

        after = None if days == -1 else datetime.now(timezone.utc) - timedelta(days=days)

        status = await message.channel.send("⏳ 메시지를 스캔하고 있습니다. 잠시만 기다려주세요...")



        channels = message.guild.text_channels

        total = len(channels)

        

        for i, ch in enumerate(channels):

            if i in exclude_indices: continue

            try:

                async for msg in ch.history(limit=None, after=after):

                    if msg.author.bot: continue

                    u = str(msg.author.id)

                    user_counts[u] = user_counts.get(u, 0) + 1

            except: continue

            if (i + 1) % 5 == 0 or i + 1 == total:

                await status.edit(content=f"진행 중... ({i+1}/{total} 채널 완료)")



        save_all_data()

        is_init = False

        await status.edit(content="✅ 스캔 완료! 모든 데이터가 저장되었습니다.")

        return



    # [랭킹 출력]

    if len(parts) == 1:

        combined = {}

        all_grouped_users = set()

        for m_set in groups.values():

            all_grouped_users.update(m_set)



        # 그룹 점수 합산

        for gname, members in groups.items():

            combined[gname] = sum(user_counts.get(str(m), 0) for m in members)



        # 개인 점수 합산 (그룹 미포함자만)

        for u, cnt in user_counts.items():

            if str(u) not in all_grouped_users:

                combined[u] = cnt



        sorted_rank = sorted(combined.items(), key=lambda x: x[1], reverse=True)

        
        result = "🏆 **메시지 랭킹**\n"

        for i, (name, cnt) in enumerate(sorted_rank[:20]):

            if str(name).isdigit():

                m = message.guild.get_member(int(name))

                display = m.display_name if m else f"유저({name})"

            else:

                display = f"👥 {name}"

            result += f"{i+1}위. {display}: **{cnt}**회\n"

        await message.channel.send(result if len(result) > 10 else "기록된 데이터가 없습니다.")

        return

    # [그래프]

    if len(parts) >= 2 and parts[1] == "그래프":

        path = make_ranking_graph(user_counts, groups, message.guild)

        await message.channel.send(file=discord.File(path))

        return

client.run(TOKEN)