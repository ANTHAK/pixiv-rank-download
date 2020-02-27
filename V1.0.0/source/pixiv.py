
import requests
from os import system, listdir
from time import sleep
from tqdm import trange
from json import load, dump
from pathlib import Path


class util:

    # 集成文件夹判断存在和创建,以及错误提出
    def create_dir(self, dirpath):
        if self.judge_file(dirpath):
            print(f"检查成功:{dirpath}")
        else:
            if self.run_cmd(f'mkdir "{dirpath}"'):
                if self.judge_file(dirpath):
                    print(f"创建成功:{dirpath}")
            else:
                print(f"存在异常字段,请检查文件夹名称是否包含不能创建文件夹的异常字段!\n{dirpath}")

    # 集成文件判断存在和创建,以及错误提出
    def create_file(self, file):
        if self.judge_file(file):
            print(f"检查成功:{file}")
        else:
            if self.run_cmd(f'type nul>"{file}"'):
                if self.judge_file(file):
                    print(f"创建成功:{file}")
            else:
                print(f"存在异常字段,请检查文件名称是否包含不能创建文件的异常字段!\n{file}")

    # 截取配置信息
    def get_config(self, data):
        return data.split("--")[-1].replace("\n", '')

    # 对目录名称还原画师ID
    def get_id(self, name):
        return int(name.split('=')[-1])

    # 判断文件或文件夹是否存在
    def judge_file(self, file_path):
        return Path(file_path).exists()

    # 只返回有无错误
    def run_cmd(self, cmd):
        r = system(cmd)
        if r == 0:
            return True
        else:
            return False


class front_control:

    def __init__(self):
        # 创建黑名单目录
        myutil.create_dir("黑名单目录")
        # 创建下载目录
        myutil.create_dir("下载")
        # 创建黑名单
        myutil.create_file("黑名单.json")
        # 创建配置文件
        myutil.create_file("config.txt")

        # 判断黑名单是否为空
        with open("黑名单.json", "r", encoding='utf-8') as fr:
            if fr.readlines():
                with open("黑名单.json", "r", encoding='utf-8') as fr:
                    self.black_user = load(fr)
                    print(f"已读取黑名单,总数:{len(self.black_user)}个")
            else:
                with open("黑名单.json", 'w', encoding='utf-8') as fw:
                    dump([], fw)
                self.black_user = load(fr)
                print("黑名单为空,对黑名单进行了初始化")

        sleep(0.01)

        # 判断黑名单目录是否为空
        black_list = listdir('黑名单目录')
        if black_list:
            print(f"检查到有黑名单需要添加,总数:{len(black_list)}")
            with trange(len(black_list)) as t:
                for i, name in zip(t, black_list):
                    ID = myutil.get_id(name)
                    # 设置进度条左边显示的信息
                    t.set_description(f"添加黑名单:{ID}")
                    if ID not in self.black_user:
                        self.black_user.append(ID)
                    sleep(0.01)
            if myutil.run_cmd("rd /s /q 黑名单目录"):
                myutil.create_dir("黑名单目录")
                print("已删除黑名单的图片")
            with open("黑名单.json", 'w', encoding='utf-8') as f:
                dump(self.black_user, f)
                print("新增黑名单已保存!")
        else:
            print("无黑名单需要添加!")

        # 配置读取
        with open("config.txt", 'r', encoding='utf-8') as fr:
            if fr.readlines():
                with open("config.txt", 'r', encoding='utf-8') as fr:
                    self.dirpath = {}
                    self.mailconfig = {}
                    config = fr.readlines()
                    for line in config:
                        if "仓库路径" in line:
                            self.dirpath["仓库"] = myutil.get_config(line)
                        elif "下载路径" in line:
                            self.dirpath["下载"] = myutil.get_config(line)
                        elif "邮件发送人" in line:
                            self.mailconfig["发送人"] = myutil.get_config(line)
                        elif "是否发送邮件" in line:
                            if line.split("--")[-1].replace("\n", '') == '是':
                                self.sendemail = True
                            else:
                                self.sendemail = False
                        elif "邮件接收人" in line:
                            self.mailconfig["接收人"] = myutil.get_config(line)
                        elif "邮箱登录的授权码" in line:
                            self.mailconfig["授权码"] = myutil.get_config(line)
                print("文件夹信息:", self.dirpath)
                if self.sendemail:
                    print("邮件配置信息", self.mailconfig)
                else:
                    print("不发送邮件")
            else:
                with open("config.txt", 'w', encoding='utf-8') as fw:
                    s = '''仓库路径(存放图片的路径)--.\下载
下载路径(下载图片的路径)--.\下载
是否发送邮件(只填写是或否,否不需要填写下面的邮件配置信息)--否
邮件发送人--
邮件接收人--
邮箱登录的授权码--'''
                    fw.write(s)
                    print(f"配置文件为空,已对配置文件进行初始化")


# 用类来进行封装
class pixiv_down:

    # 初始化一些参数
    def __init__(self):
        self.s = requests.session()  # p站爬取只能用会话才能获得返回数据
        self.s.keep_alive = False  # 设置保持连接为否
        self.native_data = []  # 存放原始数据
        self.del_li = [' ', '/', '|', '\t', '"', ':', '*', '\\', '<', '>', '?']  # windows目录删除的字符

    # 主方法
    def main_fanc(self):
        self.__get_native_data()
        self.__down_m_picture()

    # 获得原始数据,方法名前加__为私有化方法
    def __get_native_data(self):
        url = "https://www.pixiv.net/ranking.php?mode=daily&p=%d&format=json"  # 排行URL
        header = {"referer": "https://www.pixiv.net/ranking.php?mode=daily"}  # 头部跳转信息 注:应对P站防盗链,headers只需要加referer即可获得返回数据
        with trange(10) as t:
            # 循环一共有500排行, 每页50, 一共10页
            for i, p in zip(t, range(1, 11)):
                t.set_description(f"开始处理排行第{p}页的数据")  # 输出调试信息
                # 发送请求
                r = self.s.get(url % p, headers=header, timeout=30)  # timeout设置超时30秒
                r = r.json()['contents']  # 获得排行原始数据
                # 遍历原始数据
                for i in r:
                    if i["user_id"] not in mycontrol.black_user:  # 跳过黑名单
                        self.native_data.append({"p_id": i["illust_id"],  # 图片ID
                                                 "url": i["url"].replace('/c/240x480', ''),  # 图片地址还原大图地址
                                                 "u_id": i["user_id"],  # 画师ID
                                                 "u_name": self.__del_text(i["user_name"]),  # 画师昵称删除不符合的字符
                                                 "header": {"referer": f"https://www.pixiv.net/artworks/{i['illust_id']}"},  # 跳转信息
                                                 "dir_name": f'{self.__del_text(i["user_name"])}_ID={i["user_id"]}'})  # 目录名称
        sleep(0.01)
        print("排行原始数据处理完成")
        sleep(0.01)

    # 下载主图
    def __down_m_picture(self):
        with trange(len(self.native_data)) as t:
            # 循环一共有500排行, 每页50, 一共10页
            for i, data in zip(t, self.native_data):
                t.set_description(f"正在下载 画师<{data['u_name']}>的作品")  # 输出调试信息
                p_name = self.__get_p_name(data['url'])  # 获得图片的名称
                img_path = f'{mycontrol.dirpath["下载"]}\\{data["dir_name"]}\\{p_name}'
                if not self.__judge_file(f'{mycontrol.dirpath["仓库"]}\\{data["dir_name"]}\\{p_name}'):
                    if not self.__judge_file(img_path):
                        self.__create_dir(f"{mycontrol.dirpath['下载']}\\{data['dir_name']}")  # 创建画师目录
                        # 开始下载
                        img = self.s.get(data['url'], headers=data['header'])
                        self.__save_p(img.content, img_path)
                        if "p0" in data['url']:  # 判断有p0,下载子图
                            self.__down_z_picture(data)

    # 下载子图
    def __down_z_picture(self, data):
        p = 1
        while True:
            url = data['url'].replace("p0", f"p{p}")  # 替换p0
            p_name = self.__get_p_name(url)  # 获得图片的名称
            # 开始下载
            img = self.s.get(url, headers=data['header'])
            if img.status_code == 404:  # 404代码无图片了
                break  # 中断循环
            self.__save_p(img.content, f'{mycontrol.dirpath["下载"]}\\{data["dir_name"]}\\{p_name}')
            p += 1

    # 删除文本内容
    def __del_text(self, text):
        for i in self.del_li:
            text = text.replace(i, '')
        return text

    # 判断文件或文件夹是否存在
    def __judge_file(self, file_path):
        return Path(file_path).exists()

    # 创建画师目录
    def __create_dir(self, file_path):
        if not self.__judge_file(file_path):  # 创建前判断不存在
            if self.__system(f'mkdir "{file_path}"'):
                pass
                # print(f"{file_path} 创建成功")

    # 只返回有无错误
    def __system(self, cmd):
        r = system(cmd)
        if r == 0:
            return True
        else:
            return False

    # 根据url获取图片名称
    def __get_p_name(self, url):
        return url.split("/")[-1].replace("_master1200", "")

    # 保存图片
    def __save_p(self, content, file):
        with open(file, 'wb') as f:
            # 保存图片
            f.write(content)
            # print(f'{file}保存成功')


myutil = util()
mycontrol = front_control()
sleep(0.01)
pixiv_down().main_fanc()
input("程序已运行结束")