import time
import json
import os
import random
from openai import OpenAI


class Chat2DeepSeek:
    def __init__(self, api_key, model = "deepseek-reasoner"):
        self.model = model
        self.messages = [{"role": "system", "content": "You are an outstanding science fiction writer and an expert in Event Extraction of NLP"}]
        self.full_msg = [{"role": "system", "content": "You are an outstanding science fiction writer and an expert in Event Extraction of NLP"}]
        self.filename = "./log/" + str(random.randint(1, 1000)) + "user_messages_{}".format(str(time.localtime().tm_mon) + '_' + str(time.localtime().tm_mday) + '_' + str(time.localtime().tm_hour) + '_' + str(time.localtime().tm_min)) + '.json'
        self.client = OpenAI(api_key = api_key, base_url="https://api.deepseek.com")

    def ask_llm(self):
        response = self.client.chat.completions.create(
            model = self.model,
            messages = self.messages,
            stream = False,
            # response_format={ # not surpproted for now
            #     'type': 'json_object'
            #                 }
        )
        if self.model == 'deepseek-chat':
            return response.choices[0].message.content, ''
        else:
            return response.choices[0].message.content, response.choices[0].message.reasoning_content
        
    def prompt2chat(self, q):
        try:
            self.messages.append({"role": "user", "content": q})
            self.full_msg.append({"role": "user", "content": q})
            answer, reason = self.ask_llm()
            self.messages.append({"role": "assistant", "content": answer})
            self.full_msg.append({"role": "assistant", "content": answer})
            self.full_msg.append({"role": "assistant", "reasoning_content": reason})
            self.write2json()

            return answer
        except:
            self.messages = self.messages[:-1]
            self.full_msg = self.full_msg[:-1]

            return ''
        
    def write2json(self, filename=None):
        try:
            if filename:
                fn = filename
            else:
                fn = self.filename
            if not os.path.exists(fn):
                with open(fn, "w") as f:
                    pass
            with open(fn, 'r', encoding='utf-8') as f:
                content = f.read()
                msgs = json.loads(content) if len(content) > 0 else {}
            msgs.update({'user' : self.full_msg})
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(msgs, f)
        except Exception as e:
            print(f"错误代码：{e}") 