# -- encoding: utf-8 --
# @time:    	2026/10/17 下午3:13
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
import asyncio
import random
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from AgentTest.config.settings import llm
from Case_generate_Agent.agents.generate_case_agent import system_prompt
from tools import search_requirement, generator_case
checkpoint = InMemorySaver()

"""
rag知识库接入到用例生成的工作流中：
    特点：执行流程是固定的

rag知识库接用例生成的agent：
    特点：执行的步骤会更灵活，根据当前的情况动态去规划下一步的任务进行执行
    1、封装langchian工具或者(开发mcp服务）
        - 1、调用rag系统，去知识库中搜索需求文档（扩展优化封装一个专门用于需求和文档检索的agent：包含知识库检索、数据检索）
net:包含知识库检索，数据检索）
        - 2、用例生成的工具
    2、创建agent，设计agent的决策提示词
    3、调用agent去完成任务
"""
agent = create_agent(model=llm,
                     tools=[search_requirement,generator_case],
                     system_prompt=system_prompt,
                     checkpointer=checkpoint)
# create_react_agent 创建的 agent 是标准 LangGraph 图，工具在 "tools" 节点中执行时，get_stream_writer() 能正确获取到当前流的 writer，writer() 输出会作为 custom 事件传播到外层 astream
# agent = create_react_agent(llm, [search_requirement, generator_case], prompt=system_prompt, checkpointer=checkpoint)
if __name__ == '__main__':
    async def main():
        config = {"configurable": {"user_id": "jsonliu666", "thread_id": str(random.randint(1, 999999))}}
        res = agent.astream({'messages':[{'role': 'user', 'content': '获取购物车模块需求文档'}]},
                            stream_mode=['custom'],
                            config=config)
        # async for input_type, chunk in res:
        #     if input_type == 'messages':
        #         content = chunk[0].content
        #         if content:
        #             print(content, end='', flush=True)
        #     else:
        #         print(f"\n{chunk}", flush=True)
        async for input_type, chunk in res:
            print(f"\n{chunk}", flush=True)
    asyncio.run(main())
