import asyncio
import os
import socket
import sys

import aioconsole as aioconsole
from aiohttp import web
from aiohttp.abc import Request
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

## WEB HANDLER ##

def readAll(path):
    file = open(path, mode='r', encoding='utf-8')
    all_of_it = file.read()
    file.close()
    return all_of_it


resultList = ""


async def run_server(runner):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.bind(('127.0.0.1', 4343))

    await web._run_app(runner, sock=sock)


async def mainHtml(request: Request):
    return web.Response(status=200, body=readAll('main.htm'), content_type="text/html")


async def result(request: Request):
    global resultList
    transfer = resultList
    resultList = ""
    return web.Response(status=200,
                        body=transfer,
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


def newDonate(name, id=''):
    if id not in donateDict:
        print(f"새 도네이션 감지: {name}({id})")
        donateDict[id] = name
    else:
        if donateDict[id] != name:
            print(f"이름 변경 감지: {donateDict[id]} -> {name}({id}) 업데이트")
            donateDict[id] = name


def hookDonate(taID):
    dc = DesiredCapabilities.CHROME
    dc['goog:loggingPrefs'] = {'browser': 'ALL'}
    global driver

    driver = webdriver.Chrome(desired_capabilities=dc)
    driver.get(f'https://toon.at/widget/alertbox/{taID}/101')
    driver.implicitly_wait(30)

    driver.execute_script('''var origLog = console.log;
        console.log = function(obj) {
            try {
                origLog("Roll-wnwfA1hj: " + obj["content"]["account"] + "_3943_" + obj["content"]["name"])
            } catch {

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
                newDonate(name, id)
        await asyncio.sleep(1)


## CONSOLE HANDLER ##

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
        else:
            print("roong 이라고 치면 오버레이에 결과를 출력할 수 있습니다, exit 이라고 치면 종료할 수 있습니다")


## START POINT ##

if __name__ == '__main__':
    print('롤링 참치 - 투네이션 후원자 목록 박제 시스템')
    print('투네이션이 디버깅용으로 출력하는 정보를 사용해 후원자 목록을 기록합니다')
    print('이후 투네이션 시스템이 바뀌는경우 정상동작 하지 않을 수 있습니다!')
    # print('혹시라도 ChromeDriver의 버젼이 맞지 않는경우 https://sites.google.com/chromium.org/driver/ 에서')
    # print('맞는 버젼을 다운로드해서 바꿔주세요')

    if not os.path.exists('taID.txt'):
        print('taID.txt 에 투네이션 알림박스의 UUID를 입력해주세요')
        sys.exit(1)

    with open('taID.txt', 'r', encoding='utf8') as taIDFile:
        taID = taIDFile.read().strip()

    if taID == '빵바룽보':
        print('taID 를 지정해주세요, 현재 아이디는 빵바룽보입니다.')
        sys.exit(1)

    hookDonate(taID)

    print('이제 link.txt 에 있는 링크를 브라우저 소스에 추가할 수 있습니다 ^ㅅ^')
    print("roong 이라고 치면 오버레이에 결과를 출력할 수 있습니다, exit 이라고 치면 종료할 수 있습니다")

    handler = WebHandler()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    checkCoro = loop.create_task(readDonate())
    handlerCoro = loop.create_task(handler.executeUntilEnd())
    consoleCoro = loop.create_task(checkConsole())

    loop.run_until_complete(asyncio.gather(checkCoro, handlerCoro, consoleCoro))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
