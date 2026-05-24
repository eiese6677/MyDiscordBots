import discord
import json

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

APP_ID = config["application_id"]["xorgamebot"]
TOKEN = config["token"]["xorgamebot"]
