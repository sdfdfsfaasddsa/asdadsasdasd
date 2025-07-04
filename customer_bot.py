import os
import random
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

customer_count = 1
customer_profiles = {}
message_logs = {}
active_customers = {}
submit_done = set()

names = ["Placeholder01", "Placeholder02", "Placeholder03", "Placeholder04"]
special_event_name = "Special Event"

foods = [
    "Omurice", "Curry and rice", "Egg fried rice", "Ramen", "Sandwich",
    "Pancakes", "Hamburger", "Steak", "Pasta", "Spaghetti", "Crepe",
    "Dessert", "Parfait", "Ice cream", "Mochi", "Pudding", "Cake"
]

drinks = [
    "Soda", "Cream soda", "Mocktail", "Hot chocolate", "Alcohol",
    "Champagne", "Cocktail", "Coffee"
]

traits = ["SEXY", "CUTE", "FUNNY", "ELEGANT"]
talents = ["TALK", "LOVE", "SKILL", "PARTY", "HP"]
genders = ["♀ Girl", "♂ Boy"]

reaction_weights = {
    "Super bad": 5,
    "Bad": 25,
    "Average": 30,
    "Happy": 30,
    "Very happy": 10
}

reaction_replies = {
    "Super bad": [
        "SUPER BAD! The customer left very dissatisfied."
    ],
    "Bad": [
        "BAD! The customer left dissatisfied."
    ],
    "Average": [
        "AVERAGE! The customer left."
    ],
    "Happy": [
        "HAPPY! The customer left satisfied."
    ],
    "Very happy": [
       "VERY HAPPY! The customer left very satisfied."
    ]
}

GIF_URL = "https://tenor.com/qq7sBMNvdA2.gif"


def create_customer_profile(number):
    name = random.choice(names[:-1])
    if random.random() < 0.15:
        name = names[-1] + f" ⸝⸝✿ {special_event_name} ✿⸝⸝"

    return {
        "number": number,
        "name": name,
        "drink": random.choice(drinks),
        "food": random.choice(foods),
        "trait": random.choice(traits),
        "talent": random.choice(talents),
        "gender": random.choice(genders),
    }


def build_embed(profile):
    description = f"""# ⠀⠀⠀⠀⠀⠀⠀⠀︶ + ꒰CUSTOMER {profile['number']:03} 
-# ⠀⠀⠀⠀⠀⊹⠀⠀⠀⠀⠀⠀⠀requests:
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀{profile['name']} ⠀⠀⠀⠀⠀⠀⠀⊹

# ⠀  ⠀◞ ***~~✦  ~~*** **﹒** ⠀⠀⠀⠀ORDER
⠀⠀⠀+⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀{profile['drink']}⠀⠀⠀⠀⠀⠀✦✦
✦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀+ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀.
-# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⊹⠀⠀⠀⠀⠀⠀⠀⠀{profile['food']}
⠀⠀⠀⠀꒰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⊹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀;
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀︶⠀⠀LOOKING FOR: {profile['trait']} and {profile['talent']}

**~~︶︶︶︶︶︶︶︶︶~~**  {profile['gender']}⠀⠀+⠀⠀"""
    embed = discord.Embed(title="Café Customer Profile", description=description, color=discord.Color.white())
    return embed


def pick_mood_response():
    moods = list(reaction_weights.keys())
    weights = list(reaction_weights.values())
    chosen_mood = random.choices(moods, weights=weights, k=1)[0]
    reply = random.choice(reaction_replies[chosen_mood])
    return reply, chosen_mood


class CustomerView(View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.reserved_by = None

    @discord.ui.button(label="RESERVE", style=discord.ButtonStyle.primary, custom_id="reserve_btn")
    async def reserve(self, interaction: discord.Interaction, button: Button):
        if self.reserved_by is not None:
            await interaction.response.send_message("This customer is already reserved!", ephemeral=True)
            return
        self.reserved_by = interaction.user
        button.label = f"RESERVED by {interaction.user.display_name}"
        button.disabled = True
        # Enable Talk button when reserved
        for item in self.children:
            if isinstance(item, Button) and item.custom_id == "talk_btn":
                item.disabled = False
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="COMPLETED", style=discord.ButtonStyle.success, custom_id="complete_btn")
    async def complete(self, interaction: discord.Interaction, button: Button):
        if self.reserved_by is None:
            await interaction.response.send_message("You must RESERVE the customer first!", ephemeral=True)
            return
        if interaction.user != self.reserved_by:
            await interaction.response.send_message("Only the reserver can complete this!", ephemeral=True)
            return
        button.label = "COMPLETED"
        button.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="💬 Talk to Customer", style=discord.ButtonStyle.secondary, custom_id="talk_btn", disabled=True)
    async def talk(self, interaction: discord.Interaction, button: Button):
        if self.reserved_by is None:
            await interaction.response.send_message("Customer must be reserved to talk!", ephemeral=True)
            return
        if interaction.user != self.reserved_by:
            await interaction.response.send_message("Only the reserver can talk to the customer!", ephemeral=True)
            return

        customer_num = active_customers.get(self.channel_id)
        if not customer_num:
            await interaction.response.send_message("No active customer found!", ephemeral=True)
            return
        profile = customer_profiles.get(customer_num)
        if not profile:
            await interaction.response.send_message("Customer profile not found!", ephemeral=True)
            return
        msgs = message_logs.get(self.channel_id, [])
        if not msgs:
            await interaction.response.send_message("No messages found to talk about!", ephemeral=True)
            return

        reply, mood = pick_mood_response()

        embed = discord.Embed(
            title=f"{profile['name']} ({mood}) says:",
            description=reply,
            color=discord.Color.white()
        )
        embed.set_image(url=GIF_URL)

        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print("Failed to sync commands:", e)


@bot.tree.command(name="customer", description="Generate a maid cafe customer profile")
async def customer(interaction: discord.Interaction):
    global customer_count
    number = customer_count
    profile = create_customer_profile(number)
    customer_profiles[number] = profile

    embed = build_embed(profile)
    view = CustomerView(interaction.channel_id)
    await interaction.response.send_message(embed=embed, view=view)
    active_customers[interaction.channel_id] = number
    message_logs[interaction.channel_id] = []
    submit_done.discard(interaction.channel_id)
    customer_count += 1


@bot.tree.command(name="viewcustomer", description="View a previously generated customer by number")
@app_commands.describe(number="The customer number to view (e.g. 1, 2, 3...)")
async def viewcustomer(interaction: discord.Interaction, number: int):
    profile = customer_profiles.get(number)
    if not profile:
        await interaction.response.send_message(f"❌ Customer {number:03} not found.", ephemeral=True)
        return

    embed = build_embed(profile)
    view = CustomerView(interaction.channel_id)
    await interaction.response.send_message(embed=embed, view=view)
    active_customers[interaction.channel_id] = number
    message_logs[interaction.channel_id] = []
    submit_done.discard(interaction.channel_id)


@bot.tree.command(name="submit", description="Submit your conversation with the customer and unlock talk")
async def submit(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id not in active_customers:
        await interaction.response.send_message("No active customer to submit conversation for!", ephemeral=True)
        return
    if channel_id in submit_done:
        await interaction.response.send_message("You already submitted for this customer!", ephemeral=True)
        return
    submit_done.add(channel_id)

    async for message in interaction.channel.history(limit=50):
        if message.author == bot.user and message.components:
            for comp in message.components:
                for button in comp.children:
                    if button.custom_id == "talk_btn":
                        view = CustomerView(channel_id)
                        # Keep previous reserve/complete state if you want (optional)
                        # Enable talk button:
                        for item in view.children:
                            if isinstance(item, Button) and item.custom_id == "talk_btn":
                                item.disabled = False
                        try:
                            await message.edit(view=view)
                        except:
                            pass
                        break
            break

    await interaction.response.send_message("Conversation submitted! You can now use the 💬 Talk to Customer button.", ephemeral=True)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    channel_id = message.channel.id
    if channel_id in active_customers and channel_id in message_logs:
        message_logs[channel_id].append(message.content)

    await bot.process_commands(message)


client.run("MTM5MDE2MTE5OTk1MzYxMjgwMQ.G3W_wL.5adTPVG2XTAZ9NvlakexpiigZSDOskXcehLrj8")