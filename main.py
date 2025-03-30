# -*- coding: utf-8 -*-

import configparser
import os
import time
import concurrent.futures

import requests
from bs4 import BeautifulSoup

def get_text(url):
    """获取小说所有内容"""
    re_data = ''
    base_url = url.split('.html')[0]
    page_url = f"{base_url}_{{n}}.html"

    n = 1
    while True:
        current_url = page_url.format(n=n)
        response = requests.get(current_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.select_one('#container > div.row.row-detail.row-reader > div > div.reader-main > h1').text
        content = soup.select_one('#content').text
        content = content.replace('  ', '\n').replace(' ', '')

        re_data += content

        if '本章未完' not in content:
            break

        n += 1

    re_data = re_data.replace('本章未完，点击下一页继续阅读', '')
    return {'小说内容': re_data, '小说标题': title}

def get_chapters(book_url):
    """获取指定小说的每一章节"""
    response = requests.get(book_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    chapter_urls = []

    options = soup.select('#indexselect option')
    chapter_urls = [f"{URL}{option['value']}" for option in options]

    chapters = {}
    for idx, chapter_url in enumerate(chapter_urls, start=1):
        print(f'----------正在获取第{idx}页所有章节----------')
        response = requests.get(chapter_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.select('.section-list.fix')[1].select('a')
        chapters.update({f"{URL}{link['href']}": link.text for link in links})

    print('--------------所有章节地址获取完成----------------')
    return chapters

def get_book_info(soup):
    """获取每本书的信息"""
    books = []
    items = soup.select('.txt-list.txt-list-row5 li')[1:]

    for item in items:
        book = {
            '小说类型': item.select_one('.s1').text,
            '小说主角': item.select_one('.s4').text,
            '最新章节': item.select_one('.s3 a').text,
            '小说书名': item.select_one('.s2 a').text,
            '更新时间': item.select_one('.s5').text,
            '小说地址': f"{URL}{item.select_one('.s3 a')['href']}"
        }
        books.append(book)
    return books

def fetch_chapter(chapter_url):
    """获取单个章节的内容"""
    chapter_content = get_text(chapter_url)
    return chapter_content

def main(url, headers, search_data, concurrency):
    """主函数，执行爬虫逻辑"""
    try:
        search_response = requests.post(f"{url}/search/", data=search_data, headers=headers)
        search_soup = BeautifulSoup(search_response.text, 'html.parser')
        books = get_book_info(search_soup)

        for idx, book in enumerate(books):
            print('-----------------------------------')
            for key, value in book.items():
                if key == '小说地址':
                    continue
                print(f"{key} : {value}")
            print(f'选择序号 : {idx}')
            print('-----------------------------------')

        selected_book_idx = int(input('请输入您要爬取的小说序号 : '))
        selected_book = books[selected_book_idx]
        book_name = selected_book['小说书名']
        chapters = get_chapters(selected_book['小说地址'])

        n = concurrency  # 使用从配置文件中读取的并发数
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
            futures = []
            for chapter_url in chapters:
                futures.append(executor.submit(fetch_chapter, chapter_url))
                time.sleep(10)  # 在每个任务提交后暂停 10 秒

            for future in concurrent.futures.as_completed(futures):
                chapter_url = [chapter_url for chapter_url, f in zip(chapters, futures) if f == future][0]
                try:
                    chapter_content = future.result()
                    chapter_title = chapters[chapter_url]
                    clean_title = ''.join(c if c.isalnum() or c in '_ ' else '_' for c in chapter_title)
                    file_path = os.path.join(DOWNLOAD_PATH, book_name, f"{clean_title}.txt")
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    if os.path.exists(file_path):
                        print(f'文件已存在 : {file_path}')
                        continue

                    print(f'--------------正在爬取{chapter_title}----------------')
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(chapter_content['小说内容'])
                except Exception as exc:
                    print(f'{chapter_url} 生成内容时发生错误: {exc}')

    except requests.RequestException as e:
        print(f"请求失败: {e}")

def get_config():
    """读取配置文件"""
    config = configparser.ConfigParser()
    config.read('init.ini', encoding='utf-8')
    download_path = config['Paths']['dow_path']
    search_type = int(config['Paths']['search_type'].split(';')[0].strip())
    concurrency = int(config['Paths']['concurrency'].strip())  # 读取并发数配置
    return download_path, search_type, concurrency

def prepare_search_data(search_type):
    """准备搜索数据"""
    search_types = ['articlename', 'authorname']
    search_data = {
        'type': search_types[search_type],
        'searchkey': input('请输入搜索信息: ')
    }
    return search_data

if __name__ == '__main__':
    URL = 'https://www.xbqg06.com'
    HEADERS = {
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

    DOWNLOAD_PATH, SEARCH_TYPE, CONCURRENCY = get_config()
    SEARCH_DATA = prepare_search_data(SEARCH_TYPE)

    main(URL, HEADERS, SEARCH_DATA, CONCURRENCY)
