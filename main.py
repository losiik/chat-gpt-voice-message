import os

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

load_dotenv(find_dotenv())
print(os.getenv('TG_TOKEN'))
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


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

