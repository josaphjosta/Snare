import queue
import threading

# class TrackingQueue(queue.Queue):
#     def __init__(self):
#         super().__init__()
#         self._seen = set()
#         self._lock = threading.Lock()
#
#     def safe_put(self, item):
#         with self._lock:
#             if item in self._seen:
#                 return False
#             self._seen.add(item)
#             self.put(item)
#         return True
#
#     def safe_get(self, timeout=1):
#         with self._lock:
#             item = self.get(timeout=timeout)
#             if item in self._seen:
#                 self._seen.remove(item)
#         return item


class TrackingQueue(queue.Queue):
    def __init__(self, max_retry=3):  # 添加最大重试参数
        super().__init__()
        self._seen = set()
        self._retry_count = {}  # 记录事件重试次数
        self._lock = threading.Lock()
        self.max_retry = max_retry  # 最大重试次数

    def safe_put(self, item):
        with self._lock:
            # 检查是否超过重试上限
            if self._retry_count.get(item, 0) >= self.max_retry:
                return False  # 超过上限不再放入

            if item in self._seen:
                return False

            self._seen.add(item)
            # 初始化或增加重试计数
            self._retry_count[item] = self._retry_count.get(item, 0) + 1
            self.put(item)
            return True

    def safe_get(self, timeout=1):
        try:
            item = self.get(timeout=timeout)
            with self._lock:
                if item in self._seen:
                    self._seen.remove(item)  # 保持移除逻辑
            return item
        except queue.Empty:
            raise
