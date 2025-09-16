import threading
import queue
import time

from utils.util import *
from utils.TrackingQueue import TrackingQueue
from Data_generation import chat4data_all, get_local_time


API_KEY = 'sk-7015d98e24c9431f9fb7fb2a4454186e'
output_dict = {}
output_dict = load_json('./checkpoint.json')
# request_event_list = ['TRANSPORT', 'ELECT', 'START-POSITION', 'ATTACK', 'END-POSITION', 'MEET', 'MARRY', 'PHONE-WRITE',
#                   'TRANSFER-MONEY', 'SUE']

request_event_list = ['ATTACK', 'MEET', 'PHONE-WRITE', 'SUE', 'MARRY', 'TRANSPORT', 'START-POSITION', 'END-POSITION',
                      'ELECT', 'TRANSFER-MONEY', 'START-ORG', 'MERGE-ORG', 'DECLARE-BANKRUPTCY', 'END-ORG',
                      'DEMONSTRATE', 'ARREST-JAIL', 'RELEASE-PAROLE', 'TRIAL-HEARING', 'CHARGE-INDICT', 'CONVICT',
                      'SENTENCE', 'FINE', 'EXECUTE', 'EXTRADITE', 'ACQUIT', 'APPEAL', 'PARDON', 'BE-BORN', 'DIVORCE',
                      'INJURE', 'DIE', 'NOMINATE', 'TRANSFER-OWNERSHIP']

event_dict_fn = './meta_data/event_dict_full.json'
trigger_dict_fn = './meta_data/trigger_pool_augmented_5_16.json'
arguments_dict_fn = './meta_data/argument_pool_augmented_5_16.json'
arg_role_definition_fp = './meta_data/arg_roles/'

passages_per_event = 50
complex_score = 3  # not implemented
max_argument = 2
max_event = 5

weight_dict = {0: [1],
               1: [1],
               2: [0.5, 0.5],
               3: [0.2, 0.5, 0.3],
               4: [0.1, 0.2, 0.3, 0.4],
               5: [0.1, 0.1, 0.3, 0.3, 0.2]
               }

# 全局变量
NUM_THREADS = 11
 # 存储结果的字典
lock = threading.Lock()  # 用于保护对output_dict的访问
event_queue = TrackingQueue()  # 线程安全的URL队列


def fetch_url(thread_id, passages_per_event,
              event_dict_fn, trigger_dict_fn, arguments_dict_fn, arg_role_definition_fp,
              max_argument,
              max_event,
              weight_dict,
              complex_score):
    """工作线程函数，从队列获取URL并爬取内容"""

    while True:
        try:
            # 从队列获取URL，block=False表示非阻塞获取
            chat = True
            event4chat = event_queue.safe_get(timeout=1)

            try:
                with lock:
                    if event4chat in output_dict:
                        print(f"thread_id: {thread_id}\t已爬取: {event4chat}")
                        chat = False
                        event_sen = {event4chat: output_dict[event4chat]
                                     }

                if chat:
                    event_sen = chat4data_all([event4chat], passages_per_event,
                                              event_dict_fn, trigger_dict_fn, arguments_dict_fn, arg_role_definition_fp,
                                              max_argument,
                                              max_event,
                                              weight_dict,
                                              complex_score,
                                              thread_id=thread_id)

                # 使用锁保护对共享字典的访问
                with lock:
                    if not event4chat in output_dict:
                        output_dict[event4chat] = event_sen[event4chat]
                        print(f"thread_id: {thread_id}\t成功爬取: {event4chat}")
                    elif len(output_dict[event4chat]) < passages_per_event:
                        output_dict[event4chat] = event_sen[event4chat]
                        print(f"thread_id: {thread_id}\t成功爬取: {event4chat}")

            except queue.Empty:  # 专门捕获队列空异常
                print(f"thread_id: {thread_id}: 队列已空，线程退出")
                break  # 正常退出循环

            except Exception as e:
                print(f"thread_id: {thread_id}\t爬取失败: {event4chat}, 错误: {e}")
                event_queue.safe_put(event4chat)

            finally:
                event_queue.task_done()  # 标记任务完成

        except queue.Empty:
            # 队列为空，工作线程结束
            break


def main():
    # 将URL放入队列
    start_time = time.time()
    for event in request_event_list:
        event_queue.safe_put(event)

    # 创建并启动工作线程
    threads = []
    # 线程数量可根据需要调整
    num_threads = NUM_THREADS
    for i in range(num_threads):
        t = threading.Thread(target=fetch_url, args=(i, passages_per_event,
                                                     event_dict_fn, trigger_dict_fn, arguments_dict_fn,
                                                     arg_role_definition_fp,
                                                     max_argument,
                                                     max_event,
                                                     weight_dict,
                                                     complex_score))
        t.start()
        threads.append(t)

    # 等待所有URL处理完成
    event_queue.join()

    # 等待所有线程完成
    for t in threads:
        t.join()

    # 输出结果
    output_fn = './data_sen_{}.json'.format(get_local_time())
    save_json(output_dict, output_fn)
    print("\nAll threads Done, save path: {}, in {} s".format(output_fn, time.time() - start_time))


if __name__ == "__main__":
    main()
