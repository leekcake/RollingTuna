import asyncio
import os
import socket
import sys

import aioconsole as aioconsole
from aiohttp import web
from aiohttp.abc import Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

## WEB HANDLER ##
from twitch import TwitchHelix


def readAll(path):
    file = open(path, mode='r', encoding='utf-8')
    all_of_it = file.read()
    file.close()
    return all_of_it


resultList = "empty"

async def run_server(runner):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.bind(('127.0.0.1', 4343))

    await web._run_app(runner, sock=sock, print=False)


async def mainHtml(request: Request):
    return web.Response(status=200, body=readAll('main.htm'), content_type="text/html")


async def result(request: Request):
    global resultList
    transfer = resultList
    resultList = "empty"
    headers = {'Access-Control-Allow-Origin': '*'}
    return web.Response(status=200,
                        body=transfer,
                        headers=headers,
                        content_type="text/plain")


def registerResult(result):
    global resultList
    resultList = result


class WebHandler:
    def __init__(self):
        self.app = web.Application()
        self.app.add_routes([
            web.get('/', mainHtml),
            web.get('/result', result)
        ])

    async def executeUntilEnd(self):
        await run_server(self.app)
        # t = threading.Thread(target=run_server, args=(self.app,))
        # t.start()


## DONATE HANDLER ##

donateDict = {}
driver: webdriver.Chrome = None
twitch:TwitchHelix = None
twitchCache = {}

def newDonate(name, id='', type='1'):
    dName = name
    if type == '1' and twitch is not None:
        try:
            if id in twitchCache:
                dName = twitchCache[id]
            else:
                user = twitch.get_users(login_names=id)[0]
                if 'display_name' in user:
                    dName = user['display_name']
                else:
                    dName = user['name']
                twitchCache[id] = dName
        except:
            print(f"(정보 가져오기 실패) ", end='')

    if dName == name:
        print(f"도네이션 감지: {name}[{id}] ", end='')
    else:
        print(f"도네이션 감지: {name}[{dName}|{id}] ", end='')

    if id not in donateDict:
        print(f"→ 새 도네이션")
        donateDict[id] = dName
    else:
        if donateDict[id] != dName:
            print(f"→ 이름 변경 감지: {donateDict[id]} -> {dName} 업데이트")
            donateDict[id] = dName
        else:
            print("→ 필요한 작업 없음")


def hookDonate(taID):
    dc = DesiredCapabilities.CHROME
    dc['goog:loggingPrefs'] = {'browser': 'ALL'}
    global driver

    chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    chrome_options.headless = True
    driver = webdriver.Chrome(desired_capabilities=dc, options=chrome_options)
    reloadPage()

def reloadPage():
    global driver
    driver.get(f'https://toon.at/widget/alertbox/{taID}/101')
    driver.implicitly_wait(30)
    driver.execute_script('''var origLog = console.log;
            console.log = function(obj) {
                try {
                    origLog("Roll-wnwfA1hj: " + obj["content"]["account"] + "_3943_" + obj["content"]["name"] + "_3943_" + obj["content"]["acctype"])
                } catch {
                    if(obj.startsWith('ws: closed')) {
                        origLog('Roll-wsClosed');
                    }
                    if(obj.startsWith('ws: opened')) {
                        origLog(obj);
                    }
                }
            }''')


async def readDonate():
    global driver
    while True:
        for entry in driver.get_log('browser'):
            msg: str = entry['message']
            if 'Roll-wnwfA1hj: ' in msg:
                data = msg[msg.index('Roll-wnwfA1hj: '):len(msg) - 1].replace('Roll-wnwfA1hj: ', '').split('_3943_')
                id = data[0]
                name = data[1]
                type = data[2]
                newDonate(name, id, type)
            elif 'Roll-wsClosed' in msg:
                print('투네이션 알림창과의 연결이 끊긴것으로 보입니다, 새로고치는중...')
                reloadPage()
            elif 'ws: opened' in msg:
                print('투네이션 알림창과 연결된걸로 보입니다.')
        await asyncio.sleep(1)


## CONSOLE HANDLER ##

infoMessage = "명령어 목록:\n" \
              "\troong: 오버레이에 결과를 출력\n" \
              "\treload: 투네이션 알림창을 새로고침 \n" \
              "\texit: 프로그램 종료하기"

async def checkConsole():
    stdin, stdout = await aioconsole.get_standard_streams()
    async for line in stdin:
        text = line.decode('utf8').strip()
        if text.lower() == "roong":
            items = donateDict.items()
            data = {value for _, value in items}
            # print("<br>".join(data))
            registerResult("<br>".join(data))
            print("지금까지의 결과를 등록했습니다.")
        elif text.lower() == "exit":
            global driver
            driver.quit()
            sys.exit(0)
        elif text.lower() == "reload":
            reloadPage()
            print('새로고침 명령을 내렸습니다.')
        else:
            print(infoMessage)

## START POINT ##

if __name__ == '__main__':
    print('롤링 참치 - 투네이션 후원자 목록 박제 시스템 Revision 3')
    print('투네이션이 디버깅용으로 출력하는 정보를 사용해 후원자 목록을 기록합니다')
    print('이후 투네이션 시스템이 바뀌는경우 정상동작 하지 않을 수 있습니다!')
    # print('혹시라도 ChromeDriver의 버젼이 맞지 않는경우 https://sites.google.com/chromium.org/driver/ 에서')
    # print('맞는 버젼을 다운로드해서 바꿔주세요')

    if not os.path.exists('taID.txt'):
        print('taID.txt 에 투네이션 알림박스의 UUID를 입력해주세요')
        sys.exit(1)

    if not os.path.exists('token.key'):
        print('트위치 토큰이(token.key) 없습니다. 닉네임 확인기능이 비활성화됩니다')
        print('https://twitchapps.com/tokengen/ 에서 4l2zx4rx2i4ql3b3itljatzymk5gnh 를 클라이언트 아이디로 해서 토큰을 만들 수 있습니다.')
    else:
        twitch = TwitchHelix(client_id='4l2zx4rx2i4ql3b3itljatzymk5gnh', oauth_token=readAll('token.key'))

    with open('taID.txt', 'r', encoding='utf8') as taIDFile:
        taID = taIDFile.read().strip()

    if taID == '빵바룽보':
        print('taID 를 지정해주세요, 현재 아이디는 빵바룽보입니다.')
        sys.exit(1)

    hookDonate(taID)
    print(infoMessage)

    handler = WebHandler()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    checkCoro = loop.create_task(readDonate())
    handlerCoro = loop.create_task(handler.executeUntilEnd())
    consoleCoro = loop.create_task(checkConsole())

    loop.run_until_complete(asyncio.gather(checkCoro, handlerCoro, consoleCoro))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
