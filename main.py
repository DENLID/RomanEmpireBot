from typing import Optional
import disnake
from disnake.ext import commands
from pymongo import MongoClient
from PIL import Image, ImageFont, ImageDraw
import requests, io
import config

bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all())

cluster = MongoClient(config.mongo_api)
users = cluster.DB.users


class Registration(disnake.ui.Modal):
    def __init__(self):
        self.channel = bot.get_channel(1220063208564326451)
        components = [
            disnake.ui.TextInput(
                label="USERNAME",
                placeholder="Ваш никнейм в майнкрафте",
                custom_id="username"
            ),
            disnake.ui.TextInput(
                label="TOWN",
                placeholder="Ваш город в майнкрафте (Рим, Пьемонт, Сардиния)",
                custom_id="town"
            )
        ]

        super().__init__(title="Registration", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        embed = disnake.Embed(title="New member!")
        for key, value in inter.text_values.items():
            embed.add_field(
                name=key.capitalize(),
                value=value[:1024],
                inline=False
            )
        await self.channel.send(embed=embed, view=AcceptView())
        await inter.response.send_message(f"Заявка на гражданство отправлена!", ephemeral=True)

class AcceptView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.value = Optional[bool]

    @disnake.ui.button(label='Принять', style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
        await inter.response.edit_message(embed=disnake.Embed(title="Запрос принят"), view=None)
        self.value = True
        self.stop()

    @disnake.ui.button(label='Отклонить', style=disnake.ButtonStyle.red)
    async def decline(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
        await inter.response.edit_message(embed=disnake.Embed(title="Запрос отклонен"), view=None)
        self.value = False
        self.stop()


@bot.event
async def on_ready():
    print(f"Bot {bot.user} is ready to work!")
    await bot.change_presence(status=disnake.Status.online, activity=disnake.Activity(name="卐AVE ROME卐"))

@bot.event
async def on_member_join(member):
    channel_hi = bot.get_channel(1219712944003092521)
    channel_bot = bot.get_channel(1220027360242434170)
    role = member.guild.get_role(1219709622877814976)
    user = await bot.fetch_user(member.id)

    embed = disnake.Embed(
        title=f"Добро пожаловать!",
        description=f"Приветствую, {user.mention}! Что бы зарегистрироваться перейди на канал {channel_bot.mention} и напиши команду /register",
        color=0xffffff
    )

    await member.add_roles(role)
    await channel_hi.send(embed=embed)

@bot.slash_command()
async def register(inter):
    await inter.response.send_modal(modal=Registration())

@bot.slash_command()
async def passport(inter, member: disnake.Member):
    role = member.guild.get_role(886574077110784000)

    img = Image.new('RGBA', (400, 200), '#232529')
    stamp = Image.open('stamp.png', 'r')
    url = str(member.avatar)

    response = requests.get(url, stream=True)
    response = Image.open(io.BytesIO(response.content))
    response = response.convert('RGBA')
    response = response.resize((100, 100), Image.LANCZOS)

    img.paste(response, (15, 15, 115, 115))

    idraw = ImageDraw.Draw(img)
    name = member.name
    id = member.id
    birthdate = member.joined_at

    headline = ImageFont.truetype('arial.ttf', size=20)
    underline = ImageFont.truetype('arial.ttf', size=12)

    idraw.text((145,15), name, font=headline)
    idraw.text((145,50), f'ID: {id}', font=underline)
    idraw.text((145,75), f'Дата рождения: {birthdate.day}.{birthdate.month}.{birthdate.year}', font=underline)

    if role in member.roles:
        img.paste(stamp, (330, 135), mask=stamp)

    img.save('passport.png')

    await inter.send(file=disnake.File(fp='passport.png'), ephemeral=True)



bot.run(config.token)