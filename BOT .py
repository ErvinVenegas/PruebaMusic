import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cola de canciones
queue = []
volume_level = 0.5  # 50% de volumen por defecto

# Conectarse a un canal de voz
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("¡Debes estar en un canal de voz para usar este comando!")

# Reproducir música con solo el nombre de la canción
@bot.command()
async def play(ctx, *, query):
    global volume_level
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if not voice_client or not voice_client.is_playing():
        await ctx.invoke(join)
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    ydl_opts = {
        "format": "bestaudio/best",
        "default_search": "ytsearch",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        url2 = info["entries"][0]["url"]
        title = info["entries"][0]["title"]

    await ctx.send(f"\U0001F4E2 **Reproduciendo ahora:** {title} \U0001F3B5")

    # Agregar a la cola de reproducción
    queue.append(url2)
    
    if len(queue) == 1:  # Si es la primera canción en la cola
        await play_next(ctx)

# Función para reproducir la siguiente canción en la cola
async def play_next(ctx):
    global volume_level
    if len(queue) > 0:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client:
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': f"-filter:a 'volume={volume_level}' -vn"
            }

            try:
                # Reproducir la canción
                voice_client.play(discord.FFmpegPCMAudio(queue[0], **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(on_song_end(ctx), bot.loop))
            except Exception as e:
                await ctx.send(f"❌ Error al reproducir la canción: {str(e)}")

# Función que se llama cuando la canción termina
async def on_song_end(ctx):
    if queue:
        queue.pop(0)  # Eliminar la canción que ya se reprodujo
        await play_next(ctx)

# Comando para cambiar el volumen
@bot.command()
async def volume(ctx, vol: int):
    global volume_level
    if 0 <= vol <= 100:
        volume_level = vol / 100
        await ctx.send(f"\U0001F509 **Volumen ajustado a {vol}%**")
    else:
        await ctx.send("⚠️ **El volumen debe estar entre 0 y 100**")

# Comando para silenciar la música
@bot.command()
async def mute(ctx):
    global volume_level
    volume_level = 0
    await ctx.send("🔇 **Bot silenciado**")

# Comando para reanudar la música al volumen anterior
@bot.command()
async def unmute(ctx):
    global volume_level
    volume_level = 0.5  # Volver al 50% por defecto
    await ctx.send("🔊 **Bot reactivado al 50% de volumen**")

# Salir del canal de voz
@bot.command()
async def leave(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()
    else:
        await ctx.send("No estoy en un canal de voz.")

# Iniciar el bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERROR: No se encontró el TOKEN en las variables de entorno.")
