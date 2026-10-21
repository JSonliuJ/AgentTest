# -- encoding: utf-8 --
# @time:    	2026/10/20 上午10:26
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
import os

import dotenv
from langchain_openai import ChatOpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 模型路徑
STORAGE_MANAGE_PATH = os.path.join(os.path.join(BASE_DIR, "rag"),"rag_storage")
# output
OUTPUT_PATH = os.path.join(os.path.join(BASE_DIR,'rag'),'output')

# 大模型配置
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))
# 对话模型
llm = ChatOpenAI(model=os.getenv("MODEL_V3"),
                 base_url=os.getenv("BASE_URL"),
                 api_key=os.getenv("API_KEY"))