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


import requests
import time
import xml.etree.ElementTree as ET


class AzureSpeech:
    def __init__(self,
            subscription_key: str,
            region: str,
            output_format: str='riff-16khz-16bit-mono-pcm',
            language: str='en-US',
            gender: str='Female',
            voice: str='en-US-JennyNeural',
            user_agent: str='DMW Azure Speech Module 1.0') -> None:
        
        self._subscription_key: str = subscription_key
        self._region: str = region

        self._fetch_token_url: str = f'https://{self._region}.api.cognitive.microsoft.com/sts/v1.0/issueToken'
        self._tts_url: str = f'https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1'

        self._access_token: str = ''
        self._token_exp_time: float = time.monotonic()

        self.output_format: str = output_format
        self.language: str = language
        self.gender: str = gender
        self.voice: str = voice
        self.user_agent = user_agent


    def _refresh_token(self) -> None:
        if time.monotonic() >= self._token_exp_time:
            headers = {
                'Ocp-Apim-Subscription-Key': self._subscription_key
            }

            response = requests.post(self._fetch_token_url, headers=headers)
            
            self._access_token = str(response.text)
            self._token_exp_time = time.monotonic() + (8*60) # Hard coded 8-minute expiration


    def text_to_speech(self, text: str, output_file: str):
        self._refresh_token()

        headers = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': self.output_format,
            'User-Agent': self.user_agent
        }

        speak_attrib = {
            'version': '1.0',
            'xml:lang': self.language
        }

        voice_attrib = {
            'xml:lang': self.language,
            'xml:gender': self.gender,
            'name': self.voice
        }

        ssml_root = ET.Element(
            'speak', 
            attrib=speak_attrib)

        voice_element = ET.SubElement(
            ssml_root,
            'voice',
            attrib=voice_attrib)

        voice_element.text = text

        request_content = ET.tostring(ssml_root)

        response = requests.post(url=self._tts_url, headers=headers, data=request_content)

        with open(output_file, 'wb') as f:
            f.write(response.content)
