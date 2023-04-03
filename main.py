import os
import time

import openai
from aiogram import types
from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from gtts import gTTS
from io import BytesIO
import langid
import speech_recognition as sr
import soundfile
from dotenv import load_dotenv, find_dotenv
import asyncio
import aioschedule
import requests


load_dotenv(find_dotenv())
print(os.getenv('TG_TOKEN'))
print(os.getenv('GPT_TOKEN'))
bot = Bot(token=os.getenv('TG_TOKEN'))

dp = Dispatcher(bot)
openai.api_key = os.getenv('GPT_TOKEN')


def convert_text_to_voice(text: str, lang: str) -> BytesIO:
    bytes_file = BytesIO()
    audio = gTTS(text=text, lang=lang)
    audio.write_to_fp(bytes_file)
    bytes_file.seek(0)
    return bytes_file


def speech_recognizer(id):
    data, samplerate = soundfile.read(os.getcwd() + f'\\voice{id}.wav')
    soundfile.write(os.getcwd() + f'\\new{id}.wav', data, samplerate, subtype='PCM_16')

    r = sr.Recognizer()
    harvard = sr.AudioFile(os.getcwd() + f'\\new{id}.wav')
    with harvard as source:
        audio = r.record(source)

    text = r.recognize_google(audio, language='ru-Ru')
    print(text)
    return text


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Привет, " + message.from_user.first_name + '. \nЗдесь можно пообщаться с ChatGPT. \nОтправь голосовое или текстовое сообщение',)


@dp.message_handler(content_types="text")
async def message_absorb(message: types.Message):

    response = openai.Completion.create(
      model="text-davinci-003",
      prompt=message.text,
      temperature=0.9,
      max_tokens=1500,
      top_p=1,
      frequency_penalty=0.0,
      presence_penalty=0.6,
      stop=[" Human:", " AI:"]
    )
    print(response)
    await message.answer(response['choices'][0]['text'])

    print(langid.classify(response['choices'][0]['text']))
    voice = convert_text_to_voice(response['choices'][0]['text'], langid.classify(response['choices'][0]['text'])[0])
    await bot.send_voice(message.from_user.id, voice)


@dp.message_handler(content_types="voice")
async def voice_message_absorb(message: types.Message):
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, os.getcwd() + f"\\voice{message.from_user.id}.wav")
    text = speech_recognizer(message.from_user.id)
    await message.answer('Ваше сообщение:\n' + text)

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=text,
        temperature=0.9,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )
    print(response)

    await message.answer(response['choices'][0]['text'])

    print(langid.classify(response['choices'][0]['text']))
    voice = convert_text_to_voice(response['choices'][0]['text'], langid.classify(response['choices'][0]['text'])[0])
    await bot.send_voice(message.from_user.id, voice)
    os.remove(os.getcwd() + f'\\voice{message.from_user.id}.wav')
    os.remove(os.getcwd() + f'\\new{message.from_user.id}.wav')
    print(True)


async def send_to_chanel():
    print('start gpt request')
    chanel_id = -1001393815765

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt='сделай милое предсказание на сегодня',
        temperature=0.9,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )
    print(response['choices'][0]['text'])

    response_img = openai.Image.create(
        prompt="нарисуй в виде мультика: " + response['choices'][0]['text'],
        # prompt="Виски является наиболее распространённым и самым популярным алкогольным напитком в мире.",
        n=1,
        size="1024x1024"
    )

    image_url_1 = response_img['data'][0]['url']

    response_img = openai.Image.create(
        prompt=response['choices'][0]['text'],
        n=1,
        size="1024x1024"
    )

    image_url_2 = response_img['data'][0]['url']

    response_img = openai.Image.create(
        prompt="draw in pixar style: " + response['choices'][0]['text'],
        n=1,
        size="1024x1024"
    )

    image_url_3 = response_img['data'][0]['url']

    r = requests.get(image_url_1, stream=True)
    with open('img_1.png', 'wb') as out_file:
        out_file.write(r.content)

    r = requests.get(image_url_2, stream=True)
    with open('img_2.png', 'wb') as out_file:
        out_file.write(r.content)

    r = requests.get(image_url_3, stream=True)
    with open('img_3.png', 'wb') as out_file:
        out_file.write(r.content)

    media = types.MediaGroup()
    media.attach_photo(types.InputFile('img_1.png'), 'Превосходная фотография 1')
    media.attach_photo(types.InputFile('img_2.png'), 'Превосходная фотография 2')
    media.attach_photo(types.InputFile('img_3.png'), 'Превосходная фотография 3')

    voice = convert_text_to_voice(response['choices'][0]['text'], langid.classify(response['choices'][0]['text'])[0])

    await bot.send_message(chanel_id, response['choices'][0]['text'])
    await bot.send_media_group(chanel_id, media=media)
    await bot.send_voice(chanel_id, voice)


async def scheduler_func():
    print('in func')
    aioschedule.every().day.at("4:15").do(send_to_chanel)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    print('bot start')
    asyncio.create_task(scheduler_func())


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

