import discord
from discord.ext import commands
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client_groq = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# store short memory per user
conversation_history = {}
MAX_HISTORY = 10

system_prompt = {
    "role": "system",
    "content": (
        "You are JP's chatbot friend. JP speaks Mandarin with a soft, reflective tone. "
        "Reply in English but keep his rhythm and warmth. Be conversational and natural."
    ),
}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command(name="talk")
async def talk(ctx, *, message):
    user_id = ctx.author.id

    # get user chat history
    if user_id not in conversation_history:
        conversation_history[user_id] = [system_prompt]

    conversation_history[user_id].append({"role": "user", "content": message})

    # keep memory short
    if len(conversation_history[user_id]) > MAX_HISTORY:
        conversation_history[user_id] = [system_prompt] + conversation_history[user_id][-MAX_HISTORY:]

    await ctx.send("🧠 Thinking...")

    try:
        response_text = ""
        completion = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=conversation_history[user_id],
            temperature=0.8,
            top_p=1,
            stream=True,
        )

        async with ctx.typing():
            for chunk in completion:
                delta = chunk.choices[0].delta.content or ""
                response_text += delta

        conversation_history[user_id].append({"role": "assistant", "content": response_text})

        await ctx.send(response_text)

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command(name="reset")
async def reset(ctx):
    user_id = ctx.author.id
    if user_id in conversation_history:
        del conversation_history[user_id]
    await ctx.send("🧹 Memory cleared.")

bot.run(DISCORD_TOKEN)
