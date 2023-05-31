import redis.asyncio as redis
import uvloop
from pyrogram import Client, idle, filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQuery, Message

from settings import settings
from core import log

uvloop.install()
app = Client(
    "bot",
    api_id=settings.api_id,
    api_hash=settings.api_hash,
    bot_token=settings.token,
    in_memory=settings.is_memory,
)
connection = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    auto_close_connection_pool=False,
)


async def get_role(chat_id: int):
    role_in_db = await connection.get(chat_id)
    if not role_in_db:
        return settings.role_message

    return role_in_db.decode()


@app.on_message(filters.command(['start', 'help']))
async def command_pin(client: Client, message: Message):
    await client.send_message(
        message.chat.id,
        "ChatSnitch is a chat management bot that automatically sends chat rules to new members "
        "and approves their participation."
        "\nCommands:"
        "\n/set_role <New role> - set chat role (only admin and chat)"
        "\n/role - all chat role"
        "\n\nIf you have questions, ideas, want to help, or found a bug/typo, "
        "\nwrite to: @denis_malin",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("GitHub", url="https://github.com/skar404/chat-snitch")]
            ])
    )


@app.on_message(filters.command(['ping']))
async def pong_handler(_client: Client, message: Message):
    chat = message.chat
    log.info('pong_handler chat_id=%s name=%s', chat.id, chat.title)
    await message.reply_text('pong')


@app.on_callback_query()
async def inline_query(client, query):
    command, chat_id = query.data.split(':')
    if command == 'accept':
        from_user = query.from_user.id

        try:
            await client.approve_chat_join_request(
                chat_id=chat_id,
                user_id=from_user,
            )
        except UserAlreadyParticipant:
            log.error('UserAlreadyParticipant chat_id=%s name=%s new_user=%s', chat_id, query.message.chat.title,
                      from_user)
            await query.answer('You are already in this chat!')
        log.info('accept new user chat_id=%s name=%s new_user=%s', chat_id, query.message.chat.title, from_user)

    await query.message.edit_text(await get_role(chat_id), reply_markup=None)
    await query.answer('We accepted you!')


@app.on_message(filters.command(['fake']))
async def role_message_handler(client: Client, message: Message):
    chat = message.chat
    log.info('role_message_handler chat_id=%s name=%s', chat.id, chat.title)
    await client.send_message(
        chat_id=chat.id,
        text=await get_role(chat.id),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Accept", callback_data=f"fake:{chat.id}")]
            ])
    )


@app.on_message(filters.command(['role']))
async def role_message_handler(client: Client, message: Message):
    chat_id = message.chat.id
    await client.send_message(
        chat_id=chat_id,
        text=await get_role(chat_id),
    )


@app.on_message(filters.command(['set_role']))
async def role_message_handler(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    role_text = message.text[len('/set_role '):]

    if not message.chat:
        await message.reply_text('This command only works in groups.')
        return

    if not role_text:
        return await message.reply_text('Please, enter role text.')

    admin_users = set()
    async for u in client.get_chat_members(chat_id=chat_id, filter=ChatMembersFilter.ADMINISTRATORS, limit=100):
        user = u.user
        if not user.is_bot:
            admin_users.add(user.id)

    if user_id not in admin_users:
        return await message.reply_text('Only admins can use this command.')

    await connection.set(chat_id, role_text)

    role_db = await get_role(chat_id)
    await client.send_message(
        chat_id=chat_id,
        text=f"New role: \n{role_db}",
    )


@app.on_chat_join_request()
async def join_handler(client: Client, message: Message):
    chat_id = message.chat.id
    from_user = message.from_user.id

    log.info('join_handler chat_id=%s name=%s new_user=%s message=%s', chat_id, message.chat.title, from_user, message)

    await client.send_message(
        chat_id=from_user,
        text=await get_role(chat_id),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Accept", callback_data=f"accept:{chat_id}")]
            ])
    )


async def bot():
    log.info('start app')

    await connection.ping()
    log.info('ping redis is complete')

    await app.start()
    log.info('start bot')
    await idle()
    await app.stop()
    log.info('stop app')

    await connection.close()
    # Or: await connection.close(close_connection_pool=False)
    await connection.connection_pool.disconnect()


if __name__ == '__main__':
    app.run(bot())
