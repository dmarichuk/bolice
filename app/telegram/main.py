from pyrogram import Client, filters
import asyncio

# пока что лень это в каком-то удобоваримом виде импортировать
# api_id =
# api_hash = ""
# bot_token = ""

app = Client("agressive_d_disk_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


@app.on_message(filters.photo)
async def echo(client, message):
    await client.download_media(message=message.photo, file_name=message.id)
    # await message.reply(text='Hello, World!')

# async for event in app.get_chat_event_log(chat_id=):
#     print(event)


if __name__ == '__main__':
    app.run()
