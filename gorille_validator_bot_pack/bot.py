# requirements: discord.py >= 2.3
import os
import discord
from discord.ext import commands

# ========= CONFIG (edit only if needed) =========
TOKEN = os.getenv("DISCORD_TOKEN")  # Put your token in the environment variable DISCORD_TOKEN

# Channel & Role IDs (already filled with your values)
ROLES_CHANNEL_ID = 1428829051296153720          # #rôles de guilde (où les joueurs réagissent)
VALIDATION_CHANNEL_ID = 1428829108191760556     # #validation role guilde (salon staff)
GORILLE_ROLE_ID = 1388913852707639316           # rôle staff "Gorille"
PENDING_ROLE_ID = 1428831205087907860           # rôle "En attente de validation" (ou None)

# Emoji -> Guild Role ID mapping (replace emojis if you want)
EMOJI_TO_GUILD_ROLE = {
    "⚔️": 1428838674891669705,  # Clan Tempest
    "👁️": 1389359118413725696,  # Gojo
    "🩸": 1391396576563302520,  # Kamo
    "🔮": 1411093870066008305,  # Destin
    "🏰": 1428838716641902612,  # Guilde 2
}
# ================================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True          # required to manage roles
intents.reactions = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# validation_msg_id -> {member_id, target_role_id, emoji}
PENDING_VALIDATIONS = {}

def is_validator(member: discord.Member) -> bool:
    VALIDATOR_ROLE_IDS = [
        1388913852707639316,  # 🦍 Gorille
        1428882830452326461,  # Leader Clan Gojo
        1428882689502482536,  # Leader Clan Tempest
        1428882949603983561,  # Leader Clan Guilde 2
        1428883007124668416,  # Leader Clan Kamo
        1428883088858943649,  # Leader Clan Destin
    ]
    return any(r.id in VALIDATOR_ROLE_IDS for r in member.roles)


@bot.event
async def on_ready():
    print(f"[OK] Connecté comme {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # ignore our own reactions
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        guild = await bot.fetch_guild(payload.guild_id)

    # 1) Player reacts in the roles channel -> create a validation request
    if payload.channel_id == ROLES_CHANNEL_ID:
        emoji = str(payload.emoji)
        if emoji not in EMOJI_TO_GUILD_ROLE:
            return

        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)

        # Remove the user's reaction to keep the message clean (optional)
        try:
            channel = bot.get_channel(payload.channel_id) or await bot.fetch_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            await msg.remove_reaction(payload.emoji, member)
        except Exception:
            pass

        # Add "pending" role if configured
        if PENDING_ROLE_ID:
            pending_role = guild.get_role(PENDING_ROLE_ID)
            if pending_role and pending_role not in member.roles:
                try:
                    await member.add_roles(pending_role, reason="Demande guilde en attente")
                except discord.Forbidden:
                    print("[WARN] Permissions insuffisantes pour ajouter 'En attente de validation'.")

        target_role_id = EMOJI_TO_GUILD_ROLE[emoji]
        target_role = guild.get_role(target_role_id)

        validation_channel = bot.get_channel(VALIDATION_CHANNEL_ID) or await bot.fetch_channel(VALIDATION_CHANNEL_ID)

        embed = discord.Embed(
            title="Validation de rôle de guilde",
            description=(
                f"**Membre :** {member.mention}\n"
                f"**Demande :** {emoji} → {target_role.mention if target_role else target_role_id}\n\n"
                "Un 🦍 **Gorille** peut **valider (✅)** ou **refuser (❌)**."
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"UserID: {member.id} • RoleID: {target_role_id}")

        validation_msg = await validation_channel.send(embed=embed)
        PENDING_VALIDATIONS[validation_msg.id] = {
            "member_id": member.id,
            "target_role_id": target_role_id,
            "emoji": emoji,
        }
        try:
            await validation_msg.add_reaction("✅")
            await validation_msg.add_reaction("❌")
        except Exception as e:
            print("[WARN] Impossible d'ajouter ✅/❌ sur la demande:", e)
        return

    # 2) Gorille reacts in the validation channel -> approve / reject
    if payload.channel_id == VALIDATION_CHANNEL_ID and payload.message_id in PENDING_VALIDATIONS:
        reactor = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if not is_validator(reactor):
    return


        decision = str(payload.emoji)
        data = PENDING_VALIDATIONS[payload.message_id]
        member = guild.get_member(data["member_id"]) or await guild.fetch_member(data["member_id"])
        target_role = guild.get_role(data["target_role_id"])

        channel = bot.get_channel(payload.channel_id) or await bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        async def finish(success: bool, note: str):
            color = discord.Color.green() if success else discord.Color.red()
            new_embed = discord.Embed(
                title="Validation de rôle de guilde",
                description=(
                    f"**Membre :** {member.mention}\n"
                    f"**Demande :** {data['emoji']} → {target_role.mention if target_role else data['target_role_id']}\n"
                    f"**Décision :** {note} par {reactor.mention}"
                ),
                color=color
            )
            try:
                await msg.edit(embed=new_embed)
            except Exception:
                pass
            PENDING_VALIDATIONS.pop(payload.message_id, None)

        if decision == "✅":
            # remove pending
            if PENDING_ROLE_ID:
                pending_role = guild.get_role(PENDING_ROLE_ID)
                if pending_role and pending_role in member.roles:
                    try:
                        await member.remove_roles(pending_role, reason="Validation approuvée")
                    except Exception:
                        pass
            # give target role
            try:
                if target_role and target_role not in member.roles:
                    await member.add_roles(target_role, reason="Validation guilde approuvée")
                await finish(True, "✅ **Approuvé**")
            except discord.Forbidden:
                await finish(False, "⚠️ Permissions insuffisantes pour donner le rôle")
            return

        if decision == "❌":
            # remove pending
            if PENDING_ROLE_ID:
                pending_role = guild.get_role(PENDING_ROLE_ID)
                if pending_role and pending_role in member.roles:
                    try:
                        await member.remove_roles(pending_role, reason="Validation refusée")
                    except Exception:
                        pass
            await finish(False, "❌ **Refusé**")
            return

@bot.command()
@commands.has_permissions(administrator=True)
async def ping(ctx):
    await ctx.send("Pong!")

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Erreur: variable d'environnement DISCORD_TOKEN manquante.")
    bot.run(TOKEN)
