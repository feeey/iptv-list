import os
import threading
import orjson
import requests
from multiprocessing import Manager
from urllib import request
import m3u8


def down_iptv_txt(iptv_url, file_name):
    # print(iptv_url)
    # print("正在下载: " + file_name)
    try:
        response = requests.get(iptv_url)
        if response.status_code == 200:
            with open("直播源/" + file_name.replace(".json", ".txt"), "wb") as iptv_txt:
                iptv_txt.write(response.content)
            print("已下载文件: " + iptv_txt.name)
    except Exception as e:
        print("下载失败: " + iptv_txt.name + " 错误信息为: " + str(e))


# 修改check_iptv_thread()函数，以将结果存储在共享数据结构中
def check_iptv_thread(name_play_url, result_dict):
    url = name_play_url.split(",")[1]
    try:
        # 发出HTTP请求获取M3U8文件内容
        with request.urlopen(url) as file:
            if file.status == 200:
                print("M3U8链接可正常播放:" + url)
                result_dict[name_play_url] = True
        # response = requests.get(url)
        # response.raise_for_status()
        #
        # # 解析M3U8文件
        # m3u8_obj = m3u8.loads(response.text)
        #
        # # 检查是否有有效的视频流
        # if m3u8_obj.data.get('segments'):
        #     print("M3U8链接可正常播放:" + url)
        #     result_dict[name_play_url] = True
    #     else:
    #         print("M3U8链接没有有效的视频流:"+url)
    #         result_dict[name_play_url] = False
    #         # print("M3U8链接没有有效的视频流")
    #
    # except requests.exceptions.RequestException as e:
    #     print("无法访问M3U8链接:", e)
    #     result_dict[name_play_url] = False
    except Exception as e:
        #     result_dict[name_play_url] = False
        print(name_play_url + "直播源不可用 错误信息为:", e)


# 生成节目单
def generate_playlist(file_list):
    # 定义文件结果
    result = []
    # 循环打开 json 文件
    for file_name in file_list:
        with open("节目生成模板/" + file_name + '.json', "r", encoding="utf-8") as json_file:
            json_data = json_file.read()
            template_data = orjson.loads(json_data)
            # 先往 result 数组中写入标题
            print("--------------------------------------------------")
            print(file_name)
            result.append(f"{file_name},#genre#\n")

            # 创建线程列表
            threads = []

            # 创建一个共享的字典
            manager = Manager()
            result_dict = manager.dict()

            # 对 JSON 数据进行循环
            for item in template_data:
                name = item.get("name", "")
                rules = item.get("rule", "")
                for rule in rules:
                    # 根据规则查找匹配的行并写入到 index.txt
                    current_directory = os.getcwd() + "/直播源"
                    iptv_files = os.listdir(current_directory)

                    for iptv_file in iptv_files:
                        with open(current_directory + "/" + iptv_file, "r", encoding="utf-8") as source_file:
                            for line in source_file:
                                if line.startswith(f"{rule},"):
                                    # 对line进行处理
                                    line = line.replace(f"{rule},", name + ",")
                                    # 根据逗号拆分，获取url
                                    play_url = line.split(",")[1]
                                    # 将play_url 和 name 用,号相加
                                    name_play_url = name + "," + play_url
                                    # 检测直播源是否可用
                                    # 创建线程并启动它，check_iptv_thread()函数传递给线程
                                    thread = threading.Thread(target=check_iptv_thread,
                                                              args=(name_play_url, result_dict))
                                    threads.append(thread)
            # 打印当前线程数
            print("当前线程数: " + str(len(threads)) + ",正在检测直播源是否可用")
            # 批量开启线程
            for thread in threads:
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            # 加载模板文件，按模板文件name的顺序写入到 result 数组
            for item in template_data:
                # 获取模板文件中的 name 和 rule
                name = item.get("name", "")
                for key, value in result_dict.items():
                    if key.startswith(name + ",") and value:
                        result.append(key)
                        print("(直播源可用)" + key)

            # 把数据写入到 节目列表文件夹
            with open("节目列表/" + file_name + ".txt", "w", encoding="utf-8") as output_file:
                for line in result:
                    output_file.write(line)
                # 文件写入成功
                print("已写入文件: " + file_name + ".txt")
                print("--------------------------------------------------")
                # 清空 result 数组
                result.clear()


# 读取节目列表所有文件，合并到index.txt
def merge_playlist():
    file_list = ["央视频道", "卫视频道", "广东频道", "港澳台", "少儿频道"]
    # 获取当前目录下的所有文件
    current_directory = os.getcwd() + "/节目列表"
    playlist_files = [f for f in os.listdir(current_directory) if f.endswith(".txt")]

    # 打开或创建 index.txt 文件，以覆盖模式写入
    with open("index.txt", "w", encoding="utf-8") as index_file:
        # 遍历每个文件名，按照指定顺序合并文件
        for file_name in file_list:
            if file_name + ".txt" in playlist_files:
                print("正在合并: " + file_name + ".txt")
                with open("节目列表/" + file_name + ".txt", "r", encoding="utf-8") as source_file:
                    # 读取每个节目列表文件的内容并写入到 index.txt
                    for line in source_file:
                        index_file.write(line)

    # 文件写入成功
    print("已覆盖文件: index.txt")


def main():
    file_list = ["央视频道", "卫视频道", "广东频道", "港澳台", "少儿频道"]
    get_url_json()
    get_vbox_config()
    get_iptv_list()
    generate_playlist(file_list)
    merge_playlist()


if __name__ == "__main__":
    main()
