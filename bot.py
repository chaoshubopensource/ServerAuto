import discord
from discord import app_commands
import os
import json
import asyncio
from openai import OpenAI

DISCORD_TOKEN = os.environ.get("MTQ3Nzc2Njk2NDgxNzY5NDczMQ.G3ckfM.EPSzsS7higBvuScXVDx2iFQ4pG7LD7wXnAI-lg")
DEEPSEEK_API_KEY = os.environ.get("sk-1f42f93518c442ef8a2104d040d00a96")

ai = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def gerar_estrutura_ia(tema: str) -> dict:
    prompt = f"""Você é um especialista em criar servidores Discord temáticos.
Crie uma estrutura completa de servidor Discord com tema: "{tema}"

Responda APENAS com JSON válido, sem markdown, sem explicações, neste formato exato:
{{
  "server_name": "nome criativo do servidor",
  "categories": [
    {{
      "name": "NOME DA CATEGORIA",
      "channels": [
        {{"name": "nome-do-canal", "type": "text", "topic": "descrição curta do canal"}},
        {{"name": "Nome do Canal Voz", "type": "voice"}}
      ]
    }}
  ],
  "rules": ["regra 1", "regra 2", "regra 3", "regra 4", "regra 5"]
}}

Crie entre 4 a 6 categorias bem temáticas. Misture canais de texto e voz criativos.
Nomes de texto em lowercase com hífens. Voz pode ter espaços e emojis.
Seja MUITO criativo! Tudo deve fazer sentido com o tema "{tema}"."""

    response = ai.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online como {client.user}")


@tree.command(name="server", description="Recria o servidor inteiro com base em um tema usando IA")
@app_commands.describe(tema="O tema do servidor (ex: futebol, anime, cyberpunk...)")
@app_commands.checks.has_permissions(administrator=True)
async def server_command(interaction: discord.Interaction, tema: str):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild

    await interaction.followup.send(f"🤖 Gerando estrutura com IA para o tema **{tema}**...", ephemeral=True)

    try:
        # Gera estrutura via IA
        estrutura = gerar_estrutura_ia(tema)

        # Apaga todos os canais
        for channel in guild.channels:
            try:
                await channel.delete()
                await asyncio.sleep(0.3)  # Evita rate limit
            except:
                pass

        # Renomeia o servidor
        try:
            await guild.edit(name=estrutura.get("server_name", tema))
        except:
            pass

        first_text_channel = None

        # Cria categorias e canais
        for cat_data in estrutura.get("categories", []):
            category = await guild.create_category(cat_data["name"])
            await asyncio.sleep(0.3)

            for ch_data in cat_data.get("channels", []):
                try:
                    if ch_data["type"] == "text":
                        topic = ch_data.get("topic", "")
                        ch = await guild.create_text_channel(
                            ch_data["name"],
                            category=category,
                            topic=topic
                        )
                        if first_text_channel is None:
                            first_text_channel = ch
                    elif ch_data["type"] == "voice":
                        await guild.create_voice_channel(
                            ch_data["name"],
                            category=category
                        )
                    await asyncio.sleep(0.3)
                except:
                    pass

        # Posta as regras no primeiro canal
        if first_text_channel and estrutura.get("rules"):
            rules_text = f"# 📜 Regras do Servidor\n\n"
            for i, rule in enumerate(estrutura["rules"], 1):
                rules_text += f"**{i}.** {rule}\n"
            rules_text += f"\n*Servidor gerado por IA com o tema: **{tema}***"
            await first_text_channel.send(rules_text)

            try:
                await interaction.followup.send(f"✅ Servidor recriado com sucesso! Tema: **{tema}**", ephemeral=True)
            except:
                pass

    except json.JSONDecodeError:
        await interaction.followup.send("❌ Erro ao interpretar resposta da IA. Tente novamente.", ephemeral=True)
    except Exception as e:
        try:
            await interaction.followup.send(f"❌ Erro: {e}", ephemeral=True)
        except:
            pass


@server_command.error
async def server_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Você precisa ser **administrador** para usar esse comando.", ephemeral=True)


if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN não definido!")
if not DEEPSEEK_API_KEY:
    raise ValueError("❌ DEEPSEEK_API_KEY não definido!")

client.run(DISCORD_TOKEN)
