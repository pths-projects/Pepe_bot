import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7526140678:AAEmQj0xkUeqsPJgHPmk9F8vIVEpsde5DRg"
players = {}

# URL или пути к изображениям (замените на реальные)
IMAGE_URLS = {
    "tavern": "https://example.com/tavern.jpg",
    "goblin": "https://example.com/goblin.jpg",
    "orc": "https://example.com/orc.jpg",
    "dragon": "https://example.com/dragon.jpg"
}


class Player:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.hp = 100
        self.max_hp = 100
        self.attack = 10
        self.gold = 0
        self.exp = 0
        self.exp_to_level = 50


class Enemy:
    def __init__(self, name, hp, attack, reward_gold, reward_exp, image_url):
        self.name = name
        self.hp = hp
        self.attack = attack
        self.reward_gold = reward_gold
        self.reward_exp = reward_exp
        self.image_url = image_url


enemies = {
    "Гоблин": Enemy("Гоблин", 30, 5, 10, 20, IMAGE_URLS["goblin"]),
    "Орк": Enemy("Орк", 50, 8, 20, 40, IMAGE_URLS["orc"]),
    "Дракон": Enemy("Дракон", 100, 15, 50, 100, IMAGE_URLS["dragon"]),
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in players:
        players[user_id] = Player(update.effective_user.first_name)
        await update.message.reply_photo(
            photo=IMAGE_URLS["tavern"],
            caption=f"🎮 Добро пожаловать в RPG-бот, {players[user_id].name}!\n"
                    f"🔹 Уровень: {players[user_id].level}\n"
                    f"❤️ HP: {players[user_id].hp}/{players[user_id].max_hp}\n"
                    f"⚔️ Атака: {players[user_id].attack}\n"
                    f"💰 Золото: {players[user_id].gold}\n\n"
                    "Используй /menu для выбора действия!"
        )
    else:
        await update.message.reply_text("Ты уже в игре! Используй /menu.")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in players:
        await update.message.reply_text("Сначала зарегистрируйся через /start")
        return

    keyboard = [
        [InlineKeyboardButton("⚔️ Атаковать монстра", callback_data='battle')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("🏆 Квесты", callback_data='quests')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(
        photo=IMAGE_URLS["tavern"],
        caption="🎮 Главное меню:",
        reply_markup=reply_markup
    )


async def battle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    player = players[user_id]
    enemy_name = random.choice(list(enemies.keys()))
    enemy = enemies[enemy_name]

    # Первая атака
    enemy.hp -= player.attack

    if enemy.hp <= 0:
        player.gold += enemy.reward_gold
        player.exp += enemy.reward_exp
        await query.message.reply_photo(
            photo=enemy.image_url,
            caption=f"⚔️ Ты победил {enemy_name}!\n"
                    f"💰 +{enemy.reward_gold} золота\n"
                    f"✨ +{enemy.reward_exp} опыта\n\n"
                    f"Твоё золото: {player.gold}\n"
                    f"Опыт: {player.exp}/{player.exp_to_level}"
        )
        await check_level_up(player, query)
    else:
        player.hp -= enemy.attack
        if player.hp <= 0:
            player.hp = 1
            await query.message.reply_photo(
                photo=enemy.image_url,
                caption="💀 Ты проиграл и чудом выжил! "
                        f"Осталось ❤️ {player.hp} HP."
            )
        else:
            keyboard = [
                [InlineKeyboardButton("⚔️ Атаковать снова", callback_data='battle')],
                [InlineKeyboardButton("🏃‍♂️ Сбежать", callback_data='menu')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_photo(
                photo=enemy.image_url,
                caption=f"⚔️ Битва с {enemy_name}!\n"
                        f"❤️ Твоё HP: {player.hp}\n"
                        f"🩸 HP {enemy_name}: {enemy.hp}\n\n"
                        "Выбери действие:",
                reply_markup=reply_markup
            )


async def check_level_up(player, query):
    if player.exp >= player.exp_to_level:
        player.level += 1
        player.exp = 0
        player.exp_to_level *= 2
        player.max_hp += 20
        player.hp = player.max_hp
        player.attack += 5
        await query.message.reply_photo(
            photo=IMAGE_URLS["tavern"],
            caption=f"🎉 **Уровень повышен!** 🎉\n"
                    f"🔹 Новый уровень: {player.level}\n"
                    f"❤️ Макс. HP: {player.max_hp}\n"
                    f"⚔️ Атака: {player.attack}"
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == 'battle':
        await battle(update, context)
    elif data == 'stats':
        user_id = query.from_user.id
        player = players[user_id]
        await query.message.reply_photo(
            photo=IMAGE_URLS["tavern"],
            caption=f"📊 Статистика {player.name}:\n"
                    f"🔹 Уровень: {player.level}\n"
                    f"❤️ HP: {player.hp}/{player.max_hp}\n"
                    f"⚔️ Атака: {player.attack}\n"
                    f"💰 Золото: {player.gold}\n"
                    f"✨ Опыт: {player.exp}/{player.exp_to_level}"
        )
    elif data == 'menu':
        await menu(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Ошибка: {context.error}")


def main() -> None:
    application = Application.b