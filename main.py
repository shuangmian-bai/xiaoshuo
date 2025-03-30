# -*- coding: utf-8 -*-

import configparser
import os
import time

import requests
from bs4 import BeautifulSoup

#获取小说所有内容
def get_text(url1):
    re_data = ''

    url1 = url1.split('.html')[0]
    cache = url1+'_{n}.html'

    n = 1
    while True:
        url1 = cache.replace('{n}',str(n))

        req = requests.get(url1, headers=head)
        soup = BeautifulSoup(req.text, 'html.parser')

        ti = soup.select('#container > div.row.row-detail.row-reader > div > div.reader-main > h1')[0].text

        cache2 = soup.select('#content')[0].text
        cache2 = cache2.replace('  ', '\n')

        cache2 = cache2.replace(' ', '')

        re_data += cache2

        if cache2.find('本章未完') == -1:
            break

        n += 1

    re_data = re_data.replace('本章未完，点击下一页继续阅读','')

    datas = {
        '小说内容': re_data,
        '小说标题': ti
    }

    return datas



#获取指定小说的每一章节
def get_chapter(datas):
    req = requests.get(datas['小说地址'],headers=head)
    soup = BeautifulSoup(req.text, 'html.parser')
    re_data = []

    data_list = soup.select('#indexselect')[0].select('option')
    data_list = [url+i.get('value') for i in data_list]

    sj = {

    }

    time.sleep(2)

    n = 0
    for i in data_list:
        print(f'----------正在获取第{n}页所有章节----------')
        n += 1
        req = requests.get(i,headers=head)
        soup = BeautifulSoup(req.text, 'html.parser')

        a = soup.select('.section-list.fix')[1].select('a')
        cache = {url+j.get('href'):j.text for j in a}
        sj.update(cache)

    print('--------------所有章节地址获取完成----------------')
    return sj

#获取每本书的信息
def get_book_info(soup):
    data_list = []


    root = soup.select('.txt-list.txt-list-row5')[0].select('li')[1:]

    for i in root:
        data = {

        }

        types = i.select('.s1')[0].text
        zj = i.select('.s4')[0].text
        zuixin = i.select('.s3')[0].select('a')[0].text
        name = i.select('.s2')[0].select('a')[0].text
        gxrq = i.select('.s5')[0].text
        path = url+i.select('.s3')[0].select('a')[0].get('href')

        data['小说类型'] = types
        data['小说主角'] = zj
        data['最新章节'] = zuixin
        data['小说书名'] = name
        data['更新时间'] = gxrq
        data['小说地址'] = path

        data_list.append(data)
    return data_list

def main(url, head, data):
    try:
        uri = '/search/'
        response = requests.post(url+uri, data=data, headers=head)
        soup = BeautifulSoup(response.text, 'html.parser')
        datas_list = get_book_info(soup)

        a = 0
        for datas in datas_list:
            print('-----------------------------------')
            for i in datas:
                if i == '小说地址':
                    continue
                print(f"{i} : {datas[i]}")
            print(f'选择序号 : {a}')
            a += 1
            print('-----------------------------------')
        a = int(input('请输入您要爬取的小说序号 : '))
        datas = datas_list[a]
        name = datas['小说书名']

        datas = get_chapter(datas)

        quchu = [' ','、','/']
        for j in datas:
            bt = datas[j]
            root_file_path = dow_path.format(name=name)
            file_path = root_file_path.replace('.text', '/{name}.text')
            file_path = file_path.format(name=bt)
            os.makedirs(file_path[:file_path.rfind('/')], exist_ok=True)
            if os.path.exists(file_path):
                print(f'文件已存在 : {file_path}')
                continue
            text = get_text(j)



            for n in quchu:
                bt = bt.replace(n, '_')

            print(f'--------------正在爬取{bt}----------------')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text['小说内容'])



    except requests.RequestException as e:
        print(f"请求失败: {e}")


def get_config():
    config = configparser.ConfigParser()
    config.read('init.ini', encoding='utf-8')
    dow_path = config['Paths']['dow_path']
    search_type = config['Paths']['search_type'].split(';')[0].strip()
    search_type = int(search_type)
    return dow_path, search_type


def prepare_data(search_type):
    type_list = ['articlename', 'authorname']
    data = {
        'type': type_list[search_type],
        'searchkey': ''
    }
    name = input('请输入搜索信息: ')
    data['searchkey'] = name
    return data


if __name__ == '__main__':
    url = 'https://www.xbqg06.com'
    head = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.xbqg06.com',
        'priority': 'u=0, i',
        'referer': 'https://www.xbqg06.com/',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0',
    }

    dow_path, search_type = get_config()
    data = prepare_data(search_type)

    main(url, head, data)