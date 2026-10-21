# -- encoding: utf-8 --
# @time:    	2026/10/17 下午3:22
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
# 需求检索工具
import asyncio
import random
from pathlib import Path
import dotenv
from langchain_core.tools import tool

from AgentTest.config.settings import STORAGE_MANAGE_PATH
from Case_generate_Agent.ragserver import ManageRAG
from Case_generate_Agent.workflow.case_generator_workflow import GenerateTestCaseWorkflow
from langgraph.config import get_stream_writer
async def rag_search(query: str):
    # 实例化rag对象
    manager_rag = ManageRAG()
    # 初始化rag对象
    rag = await manager_rag.init_rag(working_dir=STORAGE_MANAGE_PATH, project="web_shop")
    # 加载文档
    # await manager_rag.load_document(file_path="./document/需求说明书.md")
    # 获取文档内容
    result = ""
    try:
        res = manager_rag.search_text(query=query)
        async for chunk in res:
            result += chunk
    except Exception as e:
        print(f"RAG检索失败: {e}")
    return result

# @tool(name_or_callable="search_requirement", description="需求检索工具")
# async def search_requirement(query:str):
#     writer = get_stream_writer()
#     writer(f"【开始执行节点】：调用需求检索工具-检索关键词：{query}")
#     result = await rag_search(query=query)
#     return result
# @tool(name_or_callable="generator_case", description="用例生成工具")
# async def generator_case(requirement:str):
#     writer = get_stream_writer()
#     writer(f"【开始执行节点】：调用用例生成工具-需求文档内容：{requirement}")
#     config = {"configurable": {"user_id": "jsonliu666", "thread_id":str( random.randint(1, 999999))}}
#     main_workflow = GenerateTestCaseWorkflow().main_workflow()
#     # ainvoke()不会传播任何 writer输出。必须改用astream()才能捕获子工作流中所有节点的writer内容
#     res = main_workflow.astream(input={"input_requirement": requirement},
#                                 config=config,
#                                 stream_mode=["custom", "messages"],
#                                 subgraphs=True) # subgraphs 只适用于 astream()
#     result = []
#     async for namespace, input_type, chunk in res:
#         if input_type == "messages":
#             content = chunk[0].content
#             if content:
#                 result.append(content)
#         else:
#             # writer(chunk) # create_agent需要传播，create_react_agent，工作流节点的 writer() 已经自动传播了
#             pass
#     return "测试用例已生成完毕，请查看上方输出。"
# ... existing code ...
@tool(name_or_callable="search_requirement", description="需求检索工具")
def search_requirement(query:str):
    writer = get_stream_writer()
    writer(f"【开始执行节点】：调用需求检索工具-检索关键词：{query}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(rag_search(query=query))
    print("知识库校验结果：",result)
    return result

@tool(name_or_callable="generator_case", description="用例生成工具")
def generator_case(requirement:str):
    writer = get_stream_writer()
    writer(f"【开始执行节点】：调用用例生成工具-需求文档内容：{requirement[:100]}...")
    config = {"configurable": {"user_id": "jsonliu666", "thread_id": str(random.randint(1, 999999))}}
    main_workflow = GenerateTestCaseWorkflow().main_workflow()
    async def _run():
        res = main_workflow.astream(input={"input_requirement": requirement},
                                    config=config,
                                    stream_mode=["custom"],
                                    subgraphs=True)
        result = []
        async for namespace, input_type, chunk in res:
            writer(str(chunk))
        return result

    asyncio.run(_run())
    return "测试用例已生成完毕，请查看上方输出。"
# ... existing code ...
if __name__ == '__main__':
    async def main():
        result = await search_requirement.ainvoke({"query": "加入购物车功能文档"})
        print(result)
    asyncio.run(main())

