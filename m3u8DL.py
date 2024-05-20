# _*_ coding: utf-8 _*_
# _*_ author: anwenzen _*_
from genericpath import exists
from gevent import monkey
monkey.patch_all()

import re
import os
import re
import sys
import queue
import base64
import platform
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor
import time
import json
import datetime
from pathlib import Path
#https://m1-a1.cloud.nnpp.vip:2223/api/v/?z=4bbcd9c68c6625b5432721b6290ec694&jx=%E7%86%9F%E5%B9%B4&s1ig=11399&g=
#https://m1-a1.cloud.vving.vip:2223/api/v/?z=7468d5aae4ba551a0069655a67105999&jx=%E8%BF%BD%E5%85%89%E7%9A%84%E6%97%A5%E5%AD%90&s1ig=11399&g=
api_path = 'https://a1.m1907.top:404/api/v/?'
api_path = 'https://m1-a1.cloud.nnpp.vip:2223/api/v/?'
api_path = 'https://m1-a1.cloud.vving.vip:2223/api/v/?'
api_path = 'https://m1-a1.cloud.vving.vip:2223/api/v/?'

ffmpage_path = ""
#print(appkey)
videolib="d:\\video"

appkey = '1 7468d5aae4ba551a0069655a67105999 0814d5a17095bfc3591ccc6d13e19f58 31c496f82ffd897502f58e71c7150edf 5117f1b038516d559d873674092a53e5 e090d9a71dfabaeefd49ff1c6afcdfae a037c5fdaf8efe76bea2b4964f7b3810 15a40fd4c6c6019f8f3dba73ff9242f8 245ecfc77272f060ba74f70aac2cb805 1030abade6431f748eb120d39e107603 5d855143e6fd5d1a252ac6c34b2b7e0f 631b5f669923a20dae94bf2c5b7bd50e 3ce9fd29ae903eedd5c05c128a206681 d48dca120c2cb81c11cfa6eca509066d 22423808d4caf1c00927b1f988f8e61b 1c8af15f8706ec379353f8b04d2b4c3a 13b8fbe74943e18e4f7752b97a2e1aa7 2d1bfc246274e9ce26ef8b729154cfcb 27a9e6d51c8cbc2e461c2bc5eef2481f 07fa0067c4f80182e4fb21ff29a86f87 f132c044a68b5a642e89f9157518addb f5917cff1d8f2dc50c8e6bf1773e207d 80cbcae8041527fc77204d82c3c725fd c09c0e4fab25d3ab91d937a0e01780e7 7d7db2f324b1af7fae89ca76e6e863eb 02268e51de6c56b0da64d31ca1928446 e8e56ecaca35c6229baa93884b6b7323 bc901a8b3b752896e398a102cdbc5654 b413af76b43b1a0abc231718862417e2 924269ba54ab81a99a45abc5bab03192 4bbcd9c68c6625b5432721b6290ec694 25ae68c96cbd3899b28768aa1da17cc6'
appkey = appkey.split()[datetime.datetime.today().day]
appkey2 = datetime.datetime.today().day+11397
class ThreadPoolExecutorWithQueueSizeLimit(ThreadPoolExecutor):
    """
    实现多线程有界队列
    队列数为线程数的2倍
    """

    def __init__(self, max_workers=None, *args, **kwargs):
        super().__init__(max_workers, *args, **kwargs)
        self._work_queue = queue.Queue(max_workers * 2)


def make_sum():
    ts_num = 0
    while True:
        yield ts_num
        ts_num += 1


class M3u8Download:
    """
    :param url: 完整的m3u8文件链接 如"https://www.bilibili.com/example/index.m3u8"
    :param name: 保存m3u8的文件名 如"index"
    :param max_workers: 多线程最大线程数
    :param num_retries: 重试次数
    :param base64_key: base64编码的字符串
    """

    def __init__(self, url, name, mp4=None, host='',max_workers=64, num_retries=5, base64_key=None):
        self._url = url
        self._name = name
        self._max_workers = max_workers
        self._num_retries = num_retries
        self._file_path = os.path.join(os.getcwd(), self._name)
        if mp4==None:
            self._mp4_path = "%s\\%s" % (videolib, self._name)
        else:
            self._mp4_path = "%s\\%s" % (videolib, mp4)
        #if host != '':
        #    self._mp4_path = self._mp4_path + '.' + host
        self._front_url = None
        self._ts_url_list = []
        self._success_sum = 0
        self._ts_sum = 0
        self._byte_sum = 0
        self._start_time = time.time()
        self._avr_speed = 0
        self._last_time = time.time()
        self._key = base64.b64decode(base64_key.encode()) if base64_key else None
        self._headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}

        urllib3.disable_warnings()

        self.get_m3u8_info(self._url, self._num_retries)
        print('Downloading: %s' % self._name, 'Save path: %s' % self._file_path, sep='\n')
        with ThreadPoolExecutorWithQueueSizeLimit(self._max_workers) as pool:
            for k, ts_url in enumerate(self._ts_url_list):
                pool.submit(self.download_ts, ts_url, os.path.join(self._file_path, str(k)), self._num_retries)
        if self._success_sum == self._ts_sum:
            #input("\n按回车后开始合并视频\n")
            #time.sleep(1)
            self.output_mp4()
            self.delete_file()
            print(f"Download successfully --> {self._name}.","Total %dMB, take %d seconds, arvger speed %.2f MB/s." % (int(self._byte_sum/(1024*1024)),self._last_time-self._start_time, (self._byte_sum/(1024*1024))/(self._last_time-self._start_time)))
    
    

    def get_m3u8_info(self, m3u8_url, num_retries):
        """
        获取m3u8信息
        """
        m3u8_url = m3u8_url.strip()
        if os.path.exists(m3u8_url):
            with open(m3u8_url, "r") as f:
                pass
                m3u8_text_str = f.read()
                self.get_ts_url(m3u8_text_str)    
            pass
        else:
            try:
                with requests.get(m3u8_url, timeout=(3, 30), verify=False, headers=self._headers) as res:
                    self._front_url = res.url.split(res.request.path_url)[0]
                    if "EXT-X-STREAM-INF" in res.text:  # 判定为顶级M3U8文件
                        for line in res.text.split('\n'):
                            if "#" in line:
                                continue
                            elif line.strip()=="":
                                continue
                            elif line.startswith('http'):
                                self._url = line
                            elif line.startswith('/'):
                                self._url = self._front_url + line
                            else:
                                self._url = self._url.rsplit("/", 1)[0] + '/' + line
                        self.get_m3u8_info(self._url, self._num_retries)
                    else:
                        m3u8_text_str = res.text
                        self.get_ts_url(m3u8_text_str)
            except Exception as e:
                print(e)
                if num_retries > 0:
                    self.get_m3u8_info(m3u8_url, num_retries - 1)

    def get_ts_url(self, m3u8_text_str):
        """
        获取每一个ts文件的链接
        """
        if not os.path.exists(self._file_path):
            os.mkdir(self._file_path)
        new_m3u8_str = ''
        ts = make_sum()
        for line in m3u8_text_str.split('\n'):
            if "#" in line:
                if "EXT-X-KEY" in line and "URI=" in line:
                    if os.path.exists(os.path.join(self._file_path, 'key')):
                        continue
                    key = self.download_key(line, 5)
                    if key:
                        new_m3u8_str += f'{key}\n'
                        continue
                new_m3u8_str += f'{line}\n'
                if "EXT-X-ENDLIST" in line:
                    break
            else:
                if line.startswith('http'):
                    self._ts_url_list.append(line)
                elif line.startswith('/'):
                    self._ts_url_list.append(self._front_url + line)
                else:
                    self._ts_url_list.append(self._url.rsplit("/", 1)[0] + '/' + line)
                new_m3u8_str += (os.path.join(self._file_path, str(next(ts))) + '\n')
        self._ts_sum = next(ts)
        with open(self._file_path + '.m3u8', "wb") as f:
            if platform.system() == 'Windows':
                f.write(new_m3u8_str.encode('gbk'))
            else:
                f.write(new_m3u8_str.encode('utf-8'))
    def show_inf(self):
        speed = self._avr_speed
        if speed>1024*1024:
            speed = "%5.2f MB/s" % (speed/(1024*1024))
        elif speed>1024:
            speed = "%5d KB/s" % int(speed/1024)
        else:
            speed = "%5d  B/s" % int(speed)
        sys.stdout.write('\r[%-25s](%d/%d) %s' % ("*" * (100 * self._success_sum // self._ts_sum // 4),
                                                self._success_sum, self._ts_sum, speed))
        sys.stdout.flush()

    def download_ts(self, ts_url, name, num_retries):
        """
        下载 .ts 文件
        """
        ts_url = ts_url.split('\n')[0]
        try:
            
            if not os.path.exists(name) or os.stat(name).st_size == 0:
                with requests.get(ts_url, stream=True, timeout=(5, 60), verify=False, headers=self._headers) as res:
                    if res.status_code == 200:
                        byte_sum = 0
                        chunk = res.content
                        if chunk[0:4] == b'\x89PNG':
                            print('found fake png ts, fixed it.', end='\r')
                            pos = chunk.find(b'G@')
                            if pos>=0:
                                chunk = chunk[pos:]
                        with open(name, "wb+") as ts:

                            #for chunk in res.iter_content(chunk_size=1024):
                            if chunk:
                                byte_sum= ts.write(chunk)
                                self._byte_sum+=byte_sum
                                cur = time.time()
                                if cur-self._last_time>10:
                                    speed = byte_sum/ (cur-self._last_time)
                                else:
                                    speed = (byte_sum+(10-cur+self._last_time)*self._avr_speed)/10
                                self._avr_speed = speed
                                self._last_time = cur
                                self.show_inf()
                        self._success_sum += 1
                        """
                        cur = time.time()
                        if cur-self._last_time>10:
                            speed = byte_sum/ (cur-self._last_time)
                        else:
                            speed = (byte_sum+(10-cur+self._last_time)*self._avr_speed)/10
                        self._avr_speed = speed
                        self._last_time = cur
                        if speed>1024*1024:
                            speed = "%.2f MB/s" % (speed/(1024*1024))
                        elif speed>1024:
                            speed = "%d KB/s" % int(speed/1024)
                        else:
                            speed = "%d B/s" % int(speed)
                        sys.stdout.write('\r[%-25s](%d/%d) %s\t\t\r' % ("*" * (100 * self._success_sum // self._ts_sum // 4),
                                                               self._success_sum, self._ts_sum, speed))
                        sys.stdout.flush()
                        """
                        self.show_inf()
                    else:
                        self.download_ts(ts_url, name, num_retries - 1)
            else:
                self._success_sum += 1
        except Exception:
            if os.path.exists(name):
                os.remove(name)
            if num_retries > 0:
                self.download_ts(ts_url, name, num_retries - 1)

    def download_key(self, key_line, num_retries):
        """
        下载key文件
        """
        mid_part = re.search(r"URI=[\'|\"].*?[\'|\"]", key_line).group()
        may_key_url = mid_part[5:-1]
        if self._key:
            with open(os.path.join(self._file_path, 'key'), 'wb') as f:
                f.write(self._key)
            return f'{key_line.split(mid_part)[0]}URI="./{self._name}/key"'
        if may_key_url.startswith('http'):
            true_key_url = may_key_url
        elif may_key_url.startswith('/'):
            true_key_url = self._front_url + may_key_url
        else:
            true_key_url = self._url.rsplit("/", 1)[0] + '/' + may_key_url
        try:
            with requests.get(true_key_url, timeout=(5, 30), verify=False, headers=self._headers) as res:
                with open(os.path.join(self._file_path, 'key'), 'wb') as f:
                    f.write(res.content)
            return f'{key_line.split(mid_part)[0]}URI="./{self._name}/key"{key_line.split(mid_part)[-1]}'
        except Exception as e:
            print(e)
            if os.path.exists(os.path.join(self._file_path, 'key')):
                os.remove(os.path.join(self._file_path, 'key'))
            print("加密视频,无法加载key,揭秘失败")
            if num_retries > 0:
                self.download_key(key_line, num_retries - 1)

    def output_mp4(self):
        """
        合并.ts文件，输出mp4格式视频，需要ffmpeg
        """
        #cmd = f"ffmpeg -allowed_extensions ALL -i '{self._file_path}.m3u8' -acodec copy -vcodec copy -f mp4 '{self._file_path}.mp4'"
        cmd = f"{ffmpage_path}ffmpeg -allowed_extensions ALL  -i \"{self._file_path}.m3u8\" -c copy \"{self._mp4_path}.mp4\"" #-loglevel 0
        print("\nMerge .ts files to .mp4 file.\n",cmd)
        os.system(cmd)

    def delete_file(self):
        if exists(f"\"{self._mp4_path}.mp4\""):
            file = os.listdir(self._file_path)
            for item in file:
                os.remove(os.path.join(self._file_path, item))
            os.removedirs(self._file_path)
            os.remove(self._file_path + '.m3u8')

def url_host(url):
    url = urllib3.util.parse_url(url)
    return url.host

def fmtvideoname(name):
    
    m = re.match("\\D*(\\d+)\\D*",name)
    if m==None:return name
    g = m.groups()
    if len(g)>=1:
        return "第%02d集" % int(g[0])
    return name
    pass

def search(key):
    """
    搜索影片信息
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
    #headers = {'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
    try:
        #f5917cff1d8f2dc50c8e6bf1773e207d
        
        search_url=f"{api_path}z={appkey}&jx={key}&s1ig={appkey2}&g=pptv.10" #s1ig: 11398
        with requests.get(search_url,timeout=(5, 30), verify=False, headers=headers) as res:
            obj = json.loads(res.content)
            #print(obj['data'])
            while True:
                for i in range(len(obj['data'])):
                    episode = obj['data'][i]
                    print(f"{i+1} : {episode['name']}({url_host(episode['source']['eps'][0]['url'])}) {len(episode['source']['eps'])}集")
                i = input("请选择序号（回车返回上层）: ")
                if i=="":
                    break
                else:
                    i=int(i)-1
                episode = obj['data'][i]
                host = url_host(episode['source']['eps'][0]['url'])
                eps = episode['source']['eps']
                while True:
                    for j in range(len(eps)):
                        episode['name'] = episode['name'].replace(' ','-')
                        video = eps[j]
                        filename = f"{episode['name']}-{fmtvideoname(video['name'])}".replace(' ','-')
                        file = "%s\\%s.mp4" % (videolib, filename)
                        path = Path(videolib)
                        hasmp4 = False
                        glob = '%s*.mp4' % filename
                        for file in path.glob(glob):
                            hasmp4 = True
                            break
                            pass
                        glob = '%s\\%s' % (episode['name'],glob)
                        for file in path.glob(glob):
                            hasmp4 = True
                            break
                            pass
                        #print(f"{j}:{video['name']}","*" if os.path.exists(file) else "")
                        print(f"{j+1}:{(video['name'])}","*" if hasmp4 else "")
                    k = input("请选择序号（多个用空格分开，回车返回上层）: ")
                    if k=="":
                        break
                    else:
                        k=k.split()
                        for j in k:
                            j=int(j)-1
                            video = eps[j]
                            videoname= f"{episode['name']}-{video['name']}.{host}".replace(' ','-')
                            mp4name= f"{episode['name']}\\{episode['name']}-{fmtvideoname(video['name'])}.{host}".replace(' ','-')
                            tagdir = f"{videolib}\\{episode['name']}"
                            if exists(tagdir)==False:
                                os.mkdir(tagdir)
                            M3u8Download(name=videoname,url=video["url"],mp4=mp4name) #, host=host

            return video
    except Exception as e:
        print(e)
    pass



if __name__ == "__main__":
    pass
    while True:
        key = input("请输入影片关键字（回车退出）: ")
        if key=="":
            break
        elif key=="f":
            while True:
                m3u8path = input("请输入m3u8文件路径: ")
                if m3u8path=="":
                    break
                filename = m3u8path.split('/')[-1].split('.')[0]
                M3u8Download(name=filename,url=m3u8path)                
        elif key=="u":
            while True:
                m3u8path = input("请输入m3u8 url: ")
                if m3u8path=="":
                    break
                filename = m3u8path.split('/')[-1].split('.')[0]
                filename = re.sub("https?://","", m3u8path)
                filename = re.sub("/","_", filename)
                #print(filename)
                M3u8Download(name=filename,url=m3u8path)
        else:
            search(key)
        #print(video)
    #M3u8Download(name=video["name"],url=video["url"])
else:
    url_list = input("输入url，若同时输入多个url时要用空格分开：").split()
    name_list = input("输入name，若同时输入多个name要用空格分开：").split()
    # 如果M3U8_URL的数量 ≠ SAVE_NAME的数量
    # 下载一部电视剧时，只需要输入一个name就可以了
    sta = len(url_list) == len(name_list)
    for i, u in enumerate(url_list):
        M3u8Download(u,
                     name_list[i] if sta else f"{name_list[0]}{i + 1:02}",
                     max_workers=64,
                     num_retries=10,
                     # base64_key='5N12sDHDVcx1Hqnagn4NJg=='
                     )