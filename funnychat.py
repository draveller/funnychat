# encoding:utf-8
import random
from datetime import datetime

import pymysql
import redis

import plugins
from bridge.context import ContextType
from bridge.reply import ReplyType, Reply
from channel.chat_message import ChatMessage
from plugins import *


@plugins.register(
    name="Funnychat",
    desire_priority=30,
    desc="A entertainment type of plug-in, built-in several small games",
    version="0.1",
    author="Draveller",
)
class Funnychat(Plugin):

    def __init__(self):
        super().__init__()

        self.mysql_client: pymysql.Connection | None = None
        self.redis_client: redis.Redis | None = None
        try:
            self.config = super().load_config()
            if not self.config:
                raise "[Funnychat] config not found"

            # 读取抽签桶内容 ================================================================
            slots_file_path = os.path.join(self.path, "resources/lots.json")
            with open(slots_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.lots = json.loads(content)

            logger.info("[Funnychat] inited")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[Funnychat]初始化异常：{e}")
            raise "[Funnychat] init failed, ignore "

    def get_mysql(self):
        if self.mysql_client and self.mysql_client.open:
            return self.mysql_client

        self.mysql_client = pymysql.connect(
            **{
                'host': self.config.get('mysql').get('host'),
                'port': self.config.get('mysql').get('port'),
                'user': self.config.get('mysql').get('user'),
                'password': self.config.get('mysql').get('password'),
                'database': self.config.get('mysql').get('database')
            }
        )
        return self.mysql_client

    def get_redis(self):
        if self.redis_client and self.redis_client.ping():
            return self.redis_client

        self.redis_client = redis.Redis(
            host=self.config.get('redis').get('host'),
            port=self.config.get('redis').get('port'),
            password=self.config.get('redis').get('password'),
            db=self.config.get('redis').get('db')
        )
        return self.redis_client

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return
        msg: ChatMessage = e_context["context"]["msg"]
        trimmed_content = str.strip(e_context["context"].content)
        is_group = e_context["context"]["isgroup"]
        people_name = msg.actual_user_nickname if is_group else msg.from_user_nickname
        date_num = int(datetime.now().strftime("%Y%m%d"))

        r = self.get_redis()

        reply = Reply()
        reply.type = ReplyType.TEXT

        # 触发抽签 ================================================================
        if trimmed_content == '抽签':
            key = f'{people_name}:{date_num}'
            if r.get(key):
                reply.content = '\n今天已经抽过签了, 明天再试试吧!'
            else:
                lot = random.choice(self.lots)
                r.set(name=key, value=lot['签号'], ex=3600 * 48)
                reply.content = f"\n签号: {lot['签号']}\n福祸宫位: {lot['福祸宫位']}\n诗意: {lot['诗意']}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

        # 触发解签 ================================================================
        elif trimmed_content == '解签':
            key = f'{people_name}:{date_num}'
            lot_number = int(r.get(key))

            if lot_number:
                lot = next((element for element in self.lots if element['签号'] == lot_number), {})
                reply.content = f"\n签号: {lot['签号']}\n解曰: {lot['解曰']}\n仙机: {lot['仙机']}\n典故: {lot['典故']}\n运势: {lot['运势']}"
            else:
                reply.content = f'\n今天还没抽过签噢.'
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

        # 触发签到 ================================================================
        elif is_group and trimmed_content == '签到':
            group_name = msg.from_user_nickname

            sign_flag_key = f'{group_name}:{people_name}:{date_num}'

            if r.get(sign_flag_key):
                reply.content = '\n今天已经签过到了, 明天再试试吧!'
            else:
                r.set(name=sign_flag_key, value=1, ex=3600 * 48)
                signed_num_key = f'{group_name}:{date_num}'
                signed_num = int(r.get(signed_num_key) if r.get(signed_num_key) else 0)
                reply.content = f'\n您是本群今天第{signed_num + 1}个签到的人!'
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

        # 未触发命令, 继续程序 ================================================================
        else:
            e_context.action = EventAction.CONTINUE

# todo: 程序销毁时关闭数据库连接
