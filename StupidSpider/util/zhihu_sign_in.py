import re
import base64
import requests

from time import time
from PIL import Image
from tempfile import TemporaryFile
from http.cookiejar import LWPCookieJar

from StupidSpider.util.secret import secret
from StupidSpider.util.common import hmac_encode

SIGN_UP_PAGE = 'https://www.zhihu.com/signup'
SIGN_IN_API = 'https://www.zhihu.com/api/v3/oauth/sign_in'
AUTH_ADDRESS = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
MULTIPART_FORM = {
    'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
    'grant_type': 'password',
    'source': 'com.zhihu.web',
    'username': '',
    'password': '',
    'lang': 'en',
    'ref_source': 'homepage'
}
HEADERS = {
    'Host': 'www.zhihu.com',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15',
    'Referer': 'https://www.zhihu.com/signup?next=%2F'
}


class ZhihuUser:
    def __init__(self):
        self.__session = requests.session()
        self.__session.headers = HEADERS
        self.__session.cookies = LWPCookieJar(filename='./cookie')

    def sign_in(self, username, password, load_cookie=True):
        if load_cookie and self._load_cookie():
            return self.online_status()

        headers = HEADERS.copy()
        timestamp = str(int(time() * 1000))

        headers.update({
            'Origin': 'https://www.zhihu.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'br, gzip, deflate',
            'Accept-Language': 'en-us',
            'DNT': '1',
            'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
            'X-Xsrftoken': self.__session.get(SIGN_UP_PAGE).cookies.get('_xsrf')
        })

        MULTIPART_FORM.update({
            'username': username,
            'password': password,
            'timestamp': timestamp,
            'signature': hmac_encode(
                MULTIPART_FORM['grant_type'],
                MULTIPART_FORM['client_id'],
                MULTIPART_FORM['source'],
                timestamp
            ),
            'captcha': self._get_captcha(headers)
        })
        self.__session.post(
            SIGN_IN_API,
            data=MULTIPART_FORM,
            headers=headers
        )

        return self.online_status()

    def _load_cookie(self):
        try:
            self.__session.cookies.load(ignore_discard=True)

            return True
        except FileNotFoundError:
            return False

    def _get_captcha(self, headers):
        captcha = re.search(
            r'true',
            self.__session.get(
                AUTH_ADDRESS,
                headers=headers
            ).text
        )

        if captcha:
            auth = self.__session.put(AUTH_ADDRESS, headers=headers)
            base64_img = re.findall(
                r'"img_base64":"(.+)"',
                auth.text,
                re.S
            )[0].replace(r'\n', '')

            with TemporaryFile() as f:
                f.write(base64.b64decode(base64_img))
                Image.open(f).show()
                f.close()

            input_text = input('Captcha: ')

            self.__session.post(
                AUTH_ADDRESS,
                data={
                    'input_text': input_text
                },
                headers=headers
            )

            return input_text
        return ''

    def online_status(self):
        if self.__session.get(
                SIGN_UP_PAGE,
                allow_redirects=False
        ).status_code == 302:
            self.__session.cookies.save()

            return True
        return False


user = ZhihuUser()
print(user.sign_in(secret.ZHIHU_USERNAME, secret.ZHIHU_PASSWORD))
