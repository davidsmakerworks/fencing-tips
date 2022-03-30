# MIT License

# Copyright (c) 2022 David Rice

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import hashlib
import os
import random
import subprocess
import time

from typing import List, Optional

import RPi.GPIO as GPIO

import azurespeech

SPEECH_CACHE_PATH = '/opt/fencingtips/cache'
TIPS_FILE_PATH = '/opt/fencingtips/tips.txt'
WARNING_SOUND_PATH = '/opt/fencingtips/alarm.wav'

AZURE_SUBSCRIPTION_KEY = os.environ['AZURE_SPEECH_KEY']
AZURE_REGION = os.environ['AZURE_SPEECH_REGION']

LED_PIN = 38
BUTTON_PIN = 40

COOLDOWN_TIME = 5 # Time before buton can be pressed again
COOLDOWN_PENALTY = 5 # Time added to existing cooldown if button is pressed early

VOICES = [
        'en-US-JennyNeural', 'en-US-AriaNeural', 'en-US-CoraNeural',
        'en-US-ChristopherNeural', 'en-US-EricNeural', 'en-US-GuyNeural',
        'en-US-AnaNeural'
    ]


class Tip:
    def __init__(self, text: str, phonetic: Optional[str] = None) -> None:
        self.text: str = text
        self.phonetic: Optional[str] = phonetic


def set_volume():
    subprocess.call(['/usr/bin/amixer', 'set', 'PCM', '--', '0'], shell=False)


def speak(words: str, speech_obj: azurespeech.AzureSpeech):
    hash_key = f'{words}|{speech_obj.voice}|{speech_obj.language}|{speech_obj.gender}|{speech_obj.output_format}'.encode('cp437')

    cache_file = os.path.join(SPEECH_CACHE_PATH, hashlib.md5(hash_key).hexdigest() + '.wav')

    if (not os.path.isfile(cache_file)):
        speech_obj.text_to_speech(text=words, output_file=cache_file)

    subprocess.call(['/usr/bin/aplay', cache_file], shell=False)


def play_sound(sound_file):
    subprocess.call(['/usr/bin/aplay', sound_file], shell=False)


def init_gpio() -> None:
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def read_tips_file(filename: str) -> List[Tip]:
    tips_list: List[Tip] = []

    with open(filename, 'r') as tips_file:
        for line in tips_file:
            elements: List[str] = line.split('|')

            if len(elements) > 1:
                tips_list.append(Tip(text=elements[0], phonetic=elements[1]))
            else:
                tips_list.append(Tip(text=elements[0]))
    
    return tips_list


def main() -> None:
    init_gpio()
    set_volume()

    azspeech = azurespeech.AzureSpeech(
        subscription_key=AZURE_SUBSCRIPTION_KEY,
        region=AZURE_REGION,
        user_agent='Phoenix Falcons Fencing Tips 1.0')

    tips_list: List[Tip] = read_tips_file(TIPS_FILE_PATH)

    working_list: List[Tip] = []
    cooldown_time: float = 0
    previously_pressed: bool = False

    while True:
        if not working_list:
            working_list = tips_list.copy()
            random.shuffle(working_list)

        if time.monotonic() > cooldown_time:
            GPIO.output(LED_PIN, GPIO.HIGH)
        else:
            GPIO.output(LED_PIN, GPIO.LOW)

        if not GPIO.input(BUTTON_PIN):
            if not previously_pressed:
                if time.monotonic() > cooldown_time:
                    GPIO.output(LED_PIN, GPIO.LOW)

                    tip = random.choice(working_list)

                    azspeech.voice = random.choice(VOICES)

                    if tip.phonetic:
                        speak(words=tip.phonetic, speech_obj=azspeech)
                    else:
                        speak(words=tip.text, speech_obj=azspeech)

                    working_list.remove(tip)

                    cooldown_time = time.monotonic() + COOLDOWN_TIME
                else:
                    play_sound(WARNING_SOUND_PATH)

                    cooldown_time += COOLDOWN_PENALTY

            previously_pressed = True
        else:
            previously_pressed = False
    
    GPIO.cleanup()

if __name__ == '__main__':
    main()
