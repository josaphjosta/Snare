import threading
import queue
import time

from utils.util import *
from utils.TrackingQueue import TrackingQueue
from Trigger_generation import chat4trigger_pool_all, get_local_time


API_KEY = 'sk-7015d98e24c9431f9fb7fb2a4454186e'
output_dict = {}

work_dict_fn = './exp_data/trigger_workgroup.json'
event_dict_fn = './meta_data/event_dict_full.json'

batch = load_json(work_dict_fn)
request_list = list(batch.keys())

# 全局变量
NUM_THREADS = 40
 # 存储结果的字典
lock = threading.Lock()  # 用于保护对output_dict的访问
event_queue = TrackingQueue()  # 线程安全的URL队列


def fetch_url(thread_id, work_dict_fn, event_dict_fn):
    """工作线程函数，从队列获取URL并爬取内容"""

    while True:
        try:
            # 从队列获取URL，block=False表示非阻塞获取
            chat = True
            group4chat = event_queue.safe_get(timeout=10)

            try:
                with lock:
                    if group4chat in output_dict:
                        print(f"thread_id: {thread_id}\t已爬取: {group4chat}")
                        chat = False
                        event_sen = {group4chat: output_dict[group4chat]
                                     }

                if chat:
                    event_sen = chat4trigger_pool_all([group4chat], work_dict_fn, event_dict_fn,
                                              thread_id=thread_id)

                # 使用锁保护对共享字典的访问
                with lock:
                    if not group4chat in output_dict:
                        output_dict[group4chat] = event_sen[group4chat]
                        print(f"thread_id: {thread_id}\t成功爬取: {group4chat}")

            except queue.Empty:  # 专门捕获队列空异常
                print(f"thread_id: {thread_id}: 队列已空，线程退出")
                break  # 正常退出循环

            except Exception as e:
                print(f"thread_id: {thread_id}\t爬取失败: {group4chat}, 错误: {e}")
                event_queue.safe_put(group4chat)

            finally:
                event_queue.task_done()  # 标记任务完成
                time.sleep(1)
        except queue.Empty:
            # 队列为空，工作线程结束
            break


def main():
    # 将URL放入队列
    start_time = time.time()
    for req in request_list:
        event_queue.safe_put(req)

    # 创建并启动工作线程
    threads = []
    # 线程数量可根据需要调整
    num_threads = NUM_THREADS
    for i in range(num_threads):
        t = threading.Thread(target=fetch_url, args=(i, work_dict_fn, event_dict_fn))
        t.start()
        threads.append(t)

    # 等待所有URL处理完成
    event_queue.join()

    # 等待所有线程完成
    for t in threads:
        t.join()

    # 输出结果
    output_fn = './scout_trigger_{}.json'.format(get_local_time())
    save_json(output_dict, output_fn)
    print("\nAll threads Done, save path: {}, in {} s".format(output_fn, time.time() - start_time))


if __name__ == "__main__":
    main()
