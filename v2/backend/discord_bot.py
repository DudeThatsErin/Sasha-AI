"""
Sasha AI v2 - Discord Bot
Handles knowledge approval requests and DB management via Discord.
Run this as a separate process alongside the FastAPI backend.
"""

import asyncio
import logging
import logging.handlers
import os
import random
import re
import sys
import httpx
import discord
from discord import app_commands
from discord.ext import commands
from aiohttp import web

# Load .env manually
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
GUILD_ID = int(os.environ.get("DISCORD_GUILD_ID", "0"))
CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))
OWNER_ID = int(os.environ.get("DISCORD_OWNER_ID", "0"))
BACKEND_URL = os.environ.get("BACKEND_INTERNAL_URL", "http://127.0.0.1:8000")
NOTIFY_PORT = int(os.environ.get("DISCORD_NOTIFY_PORT", "8001"))

if not BOT_TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN not set in .env")
    sys.exit(1)

# ── Logging ───────────────────────────────────────────────────────────────────

_log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(_log_dir, exist_ok=True)

_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_info_handler = logging.handlers.RotatingFileHandler(
    os.path.join(_log_dir, "sasha_discord.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_info_handler.setLevel(logging.INFO)
_info_handler.setFormatter(_formatter)

_err_handler = logging.handlers.RotatingFileHandler(
    os.path.join(_log_dir, "sasha_discord_err.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_err_handler.setLevel(logging.WARNING)
_err_handler.setFormatter(_formatter)

logging.root.setLevel(logging.INFO)
logging.root.addHandler(_info_handler)
logging.root.addHandler(_err_handler)

logger = logging.getLogger("sasha.discord")

_notify_runner = None

STATUS_ROTATE_HOURS = float(os.environ.get("BOT_STATUS_ROTATE_HOURS", "2"))

STATUS_MESSAGES = [
    "✨ Be the energy you want to attract.",
    "☕ Espresso yourself.",
    "🌱 Growth is uncomfortable. Do it anyway.",
    "🦋 She believed she could, so she did.",
    "🔥 Start before you're ready.",
    "🌙 Rest is productive too.",
    "💡 Clarity comes from action, not thought.",
    "🎯 Done is better than perfect.",
    "🌊 Go with the flow... unless the flow is wrong.",
    "🧠 Your only limit is your mind. And maybe Wi-Fi.",
    "🌸 Bloom where you are planted.",
    "⚡ Move fast. Break nothing important.",
    "🦄 Normal is overrated.",
    "🍵 Good things take time. Tea takes 4 minutes.",
    "🌟 You don't have to be great to start, but you have to start to be great.",
    "🐢 Slow progress is still progress.",
    "💪 Hard days build strong people.",
    "🎨 Create something today, even if it's a mess.",
    "🌈 After every storm comes a rainbow. And usually good Wi-Fi.",
    "🔑 The door to success is always open. It's just heavy.",
    "🧩 You are not behind. You are on your own path.",
    "🚀 Shoot for the moon. Even if you miss, you'll land among the stars.",
    "🪴 Water yourself. You're a plant too.",
    "😴 Naps are just aggressive self-care.",
    "🎵 Life is short. Listen to the good music.",
    "🌻 Turn your face toward the sun.",
    "💬 Say kind things to yourself. You're listening.",
    "🏔️ The view is better from the top. Keep climbing.",
    "🍀 Lucky things happen to people who show up.",
    "✍️ Write it down. Make it happen.",
]


# ── Discord client ────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ── Approval button view ──────────────────────────────────────────────────────

class ApprovalView(discord.ui.View):
    def __init__(self, pending_id: int):
        super().__init__(timeout=None)
        self.pending_id = pending_id

    @discord.ui.button(label="✅ Yes, learn it", style=discord.ButtonStyle.success, custom_id="approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{BACKEND_URL}/pending-knowledge/{self.pending_id}/approve")
        if r.status_code == 200:
            await interaction.edit_original_response(
                content=interaction.message.content + "\n\n✅ **Approved!** Sasha will now know this.",
                view=None,
            )
        else:
            await interaction.followup.send(f"⚠️ Backend error: {r.text}", ephemeral=True)

    @discord.ui.button(label="❌ No, ignore it", style=discord.ButtonStyle.danger, custom_id="deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{BACKEND_URL}/pending-knowledge/{self.pending_id}/deny")
        if r.status_code == 200:
            await interaction.edit_original_response(
                content=interaction.message.content + "\n\n❌ **Denied.** Sasha won't learn this.",
                view=None,
            )
        else:
            await interaction.followup.send(f"⚠️ Backend error: {r.text}", ephemeral=True)


# ── Internal HTTP server ──────────────────────────────────────────────────────

async def handle_notify(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        pending_id = data["pending_id"]
        content = data["content"]
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            return web.json_response({"error": "Channel not found"}, status=500)
        owner_mention = f"<@{OWNER_ID}>" if OWNER_ID else "Erin"
        msg = await channel.send(
            f"{owner_mention} 🤔 Someone wants Sasha to learn something new:\n\n"
            f"> **{content}**\n\n"
            f"Should Sasha learn this?",
            view=ApprovalView(pending_id),
        )
        return web.json_response({"discord_message_id": str(msg.id)})
    except Exception as e:
        logger.error(f"Notify handler error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_widget_notify(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        message = data.get("message", "(unknown)")
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            return web.json_response({"error": "Channel not found"}, status=500)
        await channel.send(f"💬 **Widget used!** Someone asked Sasha:\n> {message[:300]}")
        return web.json_response({"ok": True})
    except Exception as e:
        logger.error(f"Widget notify handler error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def start_notify_server():
    global _notify_runner
    if _notify_runner is not None:
        logger.info("Notify server already running, skipping bind")
        return
    notify_app = web.Application()
    notify_app.router.add_post("/notify-pending", handle_notify)
    notify_app.router.add_post("/notify-widget", handle_widget_notify)
    _notify_runner = web.AppRunner(notify_app)
    await _notify_runner.setup()
    site = web.TCPSite(_notify_runner, "127.0.0.1", NOTIFY_PORT)
    await site.start()
    logger.info(f"Discord notify server listening on http://127.0.0.1:{NOTIFY_PORT}")


# ── Slash commands ────────────────────────────────────────────────────────────

@tree.command(name="knowledge-list", description="List Sasha's knowledge entries", guilds=[discord.Object(id=GUILD_ID)])
async def knowledge_list(interaction: discord.Interaction, category: str = "ALL"):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BACKEND_URL}/knowledge")
    if r.status_code != 200:
        await interaction.followup.send("⚠️ Could not reach backend.", ephemeral=True)
        return
    entries = r.json()
    if category != "ALL":
        entries = [e for e in entries if e["category"].upper() == category.upper()]
    if not entries:
        await interaction.followup.send("No entries found.", ephemeral=True)
        return
    grouped: dict[str, list] = {}
    for e in entries:
        grouped.setdefault(e["category"], []).append(e)
    lines = []
    for cat, items in grouped.items():
        lines.append(f"**{cat}**")
        for item in items:
            status = "✓" if item["is_active"] else "○"
            lines.append(f"  `{item['id']}` {status} {item['content'][:80]}")
        lines.append("")
    text = "\n".join(lines)
    if len(text) > 1900:
        text = text[:1900] + "\n…(truncated)"
    await interaction.followup.send(text, ephemeral=True)


@tree.command(name="knowledge-add", description="Add a new knowledge entry for Sasha", guilds=[discord.Object(id=GUILD_ID)])
@app_commands.describe(category="Category (e.g. TECH STACK)", content="The fact to add")
async def knowledge_add(interaction: discord.Interaction, category: str, content: str):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{BACKEND_URL}/knowledge",
            json={"category": category.upper(), "content": content, "sort_order": 0},
        )
    if r.status_code == 201:
        data = r.json()
        await interaction.followup.send(
            f"✅ Added entry `{data['id']}` under **{data['category']}**:\n> {data['content']}",
            ephemeral=True,
        )
    else:
        await interaction.followup.send(f"⚠️ Error: {r.text}", ephemeral=True)


@tree.command(name="knowledge-delete", description="Delete a knowledge entry by ID", guilds=[discord.Object(id=GUILD_ID)])
@app_commands.describe(entry_id="The numeric ID of the entry to delete")
async def knowledge_delete(interaction: discord.Interaction, entry_id: int):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.delete(f"{BACKEND_URL}/knowledge/{entry_id}")
    if r.status_code == 200:
        await interaction.followup.send(f"🗑️ Entry `{entry_id}` deleted.", ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ Error: {r.text}", ephemeral=True)


@tree.command(name="knowledge-toggle", description="Enable or disable a knowledge entry", guilds=[discord.Object(id=GUILD_ID)])
@app_commands.describe(entry_id="The numeric ID of the entry", active="True to enable, False to disable")
async def knowledge_toggle(interaction: discord.Interaction, entry_id: int, active: bool):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.put(f"{BACKEND_URL}/knowledge/{entry_id}", json={"is_active": active})
    if r.status_code == 200:
        state = "enabled ✅" if active else "disabled ○"
        await interaction.followup.send(f"Entry `{entry_id}` is now {state}.", ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ Error: {r.text}", ephemeral=True)


@tree.command(name="knowledge-rebuild", description="Rebuild Sasha's RAG vector index", guilds=[discord.Object(id=GUILD_ID)])
async def knowledge_rebuild(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BACKEND_URL}/knowledge/rebuild-index")
    if r.status_code == 200:
        data = r.json()
        await interaction.followup.send(f"🔄 {data['message']}", ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ Error: {r.text}", ephemeral=True)


@tree.command(name="pending-list", description="List pending knowledge awaiting approval", guilds=[discord.Object(id=GUILD_ID)])
async def pending_list(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BACKEND_URL}/pending-knowledge")
    if r.status_code != 200:
        await interaction.followup.send("⚠️ Could not reach backend.", ephemeral=True)
        return
    entries = [e for e in r.json() if e["status"] == "pending"]
    if not entries:
        await interaction.followup.send("No pending entries.", ephemeral=True)
        return
    lines = ["**Pending Knowledge Requests:**"]
    for e in entries:
        lines.append(f"`{e['id']}` — {e['content'][:100]}")
    await interaction.followup.send("\n".join(lines), ephemeral=True)


@tree.command(name="pending-approve", description="Approve a pending knowledge entry by ID", guilds=[discord.Object(id=GUILD_ID)])
@app_commands.describe(entry_id="The numeric ID of the pending entry")
async def pending_approve(interaction: discord.Interaction, entry_id: int):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{BACKEND_URL}/pending-knowledge/{entry_id}/approve")
    if r.status_code == 200:
        await interaction.followup.send(f"✅ Entry `{entry_id}` approved and added to knowledge base.", ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ Error: {r.text}", ephemeral=True)


@tree.command(name="pending-deny", description="Deny a pending knowledge entry by ID", guilds=[discord.Object(id=GUILD_ID)])
@app_commands.describe(entry_id="The numeric ID of the pending entry")
async def pending_deny(interaction: discord.Interaction, entry_id: int):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{BACKEND_URL}/pending-knowledge/{entry_id}/deny")
    if r.status_code == 200:
        await interaction.followup.send(f"❌ Entry `{entry_id}` denied.", ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ Error: {r.text}", ephemeral=True)


@tree.command(name="rag-status", description="Check the RAG vector index status", guilds=[discord.Object(id=GUILD_ID)])
async def rag_status_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BACKEND_URL}/rag/status")
    if r.status_code == 200:
        data = r.json()
        enabled = "✅ Enabled" if data.get("rag_enabled") else "⚠️ Disabled (fallback mode)"
        msg = (
            f"**RAG Status:** {enabled}\n"
            f"**Embed model:** `{data.get('embed_model', 'N/A')}`\n"
            f"**Indexed entries:** `{data.get('indexed_entries', 0)}`\n"
            f"**Top-K:** `{data.get('top_k', 'N/A')}`"
        )
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ Error: {r.text}", ephemeral=True)


# ── OneNote link parser ───────────────────────────────────────────────────────

_ONENOTE_RE = re.compile(r'onenote:[^\s>)"\']+', re.IGNORECASE)
_HTTPS_RE = re.compile(r'https://[^\s>)"\']+', re.IGNORECASE)


@bot.event
async def on_message(message: discord.Message):
    """Handle DMs: if the message contains a OneNote link, split and echo both URLs."""
    if message.author.bot:
        return
    if not isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)
        return

    content = message.content.strip()
    logger.info(f"DM received from {message.author}: {repr(content[:200])}")

    onenote_urls = _ONENOTE_RE.findall(content)
    https_urls = _HTTPS_RE.findall(content)
    logger.info(f"OneNote URLs: {onenote_urls} | HTTPS URLs: {https_urls}")

    if not onenote_urls:
        await bot.process_commands(message)
        return

    # Deduplicate while preserving order; prefer d.docs.live.net over view.aspx when both present
    seen = set()
    deduped_https: list[str] = []
    for url in https_urls:
        if url not in seen:
            seen.add(url)
            deduped_https.append(url)
    # If we have both a view.aspx and a d.docs.live.net URL, drop the view.aspx one
    live_net = [u for u in deduped_https if "d.docs.live.net" in u]
    view_aspx = [u for u in deduped_https if "d.docs.live.net" not in u]
    if live_net and view_aspx:
        deduped_https = live_net  # keep only the cleaner direct link

    lines: list[str] = []

    lines.append("**In-app link** (opens OneNote desktop):")
    for url in onenote_urls:
        lines.append(f"```\n{url}\n```")
        lines.append(f"[Click to open in OneNote](<{url}>)")

    if deduped_https:
        lines.append("\n**Web link** (opens in browser):")
        for url in deduped_https:
            lines.append(f"```\n{url}\n```")
            lines.append(f"[Click to open in browser](<{url}>)")
    else:
        lines.append("_No https:// link found in that paste._")

    await message.reply("\n".join(lines), mention_author=False)
    await bot.process_commands(message)


# ── Rotating status task ─────────────────────────────────────────────────────

async def rotate_status():
    await bot.wait_until_ready()
    used: list[str] = []
    while not bot.is_closed():
        remaining = [s for s in STATUS_MESSAGES if s not in used]
        if not remaining:
            used.clear()
            remaining = STATUS_MESSAGES[:]
        choice = random.choice(remaining)
        used.append(choice)
        await bot.change_presence(activity=discord.CustomActivity(name=choice))
        logger.info(f"Status updated to: {choice}")
        await asyncio.sleep(STATUS_ROTATE_HOURS * 3600)


# ── Bot events ────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    logger.info(f"Sasha Discord bot (v2) logged in as {bot.user} (ID: {bot.user.id})")
    await start_notify_server()
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    logger.info(f"Slash commands synced to guild {GUILD_ID}")
    bot.loop.create_task(rotate_status())


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import socket
    import time

    max_wait = 300
    delay = 5
    waited = 0
    while waited < max_wait:
        try:
            socket.setdefaulttimeout(5)
            socket.getaddrinfo("discord.com", 443)
            break
        except OSError:
            logger.warning(f"Network not ready, retrying in {delay}s...")
            time.sleep(delay)
            waited += delay
            delay = min(delay * 2, 60)
    else:
        logger.error("Network unavailable after 5 minutes, exiting.")
        sys.exit(1)

    bot.run(BOT_TOKEN)
