# -- encoding: utf-8 --
# @time:    	2026/10/12 下午6:04
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
import os
import dotenv
import httpx
import asyncio
import hashlib
import numpy as np
from typing import Any, List, Dict
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything

from AgentTest.config.settings import OUTPUT_PATH, BASE_DIR

"""
RAG-Anything工具库：
    1、多种格式文件文档解析的功能
    2、配置视觉模型，它可以基于视觉模型对文档中图片表格等等相关的信息进行分析，
    3、创建知识关联的知识图谱
# 基础安装
pip install raganything
# 安装包含扩展格式支持的可选依赖：
pip install 'raganything[all]'              # 所有可选功能
pip install 'raganything[image]'            # 图像格式转换 (BMP, TIFF, GIF, WebP)
pip install 'raganything[text]'             # 文本文件处理 (TXT, MD)
pip install 'raganything[image,text]'       # 多个功能组合
pip install "mineru[pipeline]"              # MinerU 需要安装本地推理引擎依赖（包含 PyTorch）
"""

dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))

# 1、定义llm对话的处理函数（一定要定义成异步函数）
async def llm_model_func(
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list[dict[str, Any]] | None = None,
        enable_cot: bool = False,
        token_tracker: Any | None = None,
        stream: bool | None = None,
        timeout: int | None = None,
        keyword_extraction: bool = False,
        use_azure: bool = False,
        azure_deployment: str | None = None,
        api_version: str | None = None,
        **kwargs: Any) -> str:
    chinese_instruction = """
                           输出规范：
                               - 必须使用中文回复
                               - 只返回知识库检索到的内容
                               - 不要翻译成其他语言
                       """
    if system_prompt:
        system_prompt = system_prompt + "\n\n" + chinese_instruction
    else:
        system_prompt = f"""你是一个资深的知识检索助手，请根据用户的问题进行分析去知识库检索结果
                            {chinese_instruction}
                        """
    return await openai_complete_if_cache(
        model=os.getenv("MODEL_V3"),
        base_url=os.getenv("BASE_URL"),
        api_key=os.getenv("API_KEY"),
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        enable_cot=enable_cot,
        token_tracker=token_tracker,
        stream=stream,
        timeout=timeout,
        keyword_extraction=keyword_extraction,
        use_azure=use_azure,
        azure_deployment=azure_deployment,
        api_version=api_version,
        **kwargs
    )


# 2、定义embedding函数（一定要定义成异步函数）
async def embedding_model_func(
        texts: list[str],
        embedding_dim: int | None = None,
        max_token_size: int | None = None,
        client_configs: dict[str, Any] | None = None,
        token_tracker: Any | None = None,
        use_azure: bool = False,
        azure_deployment: str | None = None,
        api_version: str | None = None,
        context: str = "document",
        query_prefix: str | None = None,
        document_prefix: str | None = None) -> np.ndarray:
    return await openai_embed.func(
        texts=texts,
        model=os.getenv("EMBEDDING_MODEL_QW3-8B"),
        base_url=os.getenv("BASE_URL"),
        api_key=os.getenv("API_KEY"),
        embedding_dim=embedding_dim,
        max_token_size=max_token_size,
        client_configs=client_configs,
        token_tracker=token_tracker,
        use_azure=use_azure,
        azure_deployment=azure_deployment,
        api_version=api_version,
        context=context,
        query_prefix=query_prefix,
        document_prefix=document_prefix
    )


# 3、定义重排序函数（一定要定义成异步函数）
async def custom_rerank_func(query, documents, top_n=None) -> List[Dict[str, Any]]:
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    payload = {
        "model": os.getenv("RERANK_MODEL"),
        "query": query,
        "documents": list(documents),
        "return_documents": False
    }
    if top_n:
        payload["top_n"] = top_n

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{base_url}/rerank",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    return [
        {
            "index": item["index"],
            "score": item.get("relevance_score", 0.0),
            "text": documents[item["index"]],
        }
        for item in results
    ]


# 定义视觉模型
async def vision_model_func(
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list[dict[str, Any]] | None = None,
        image_data=None,
        **kwargs: Any
) -> str:
    """视觉模型嵌入处理函数"""
    # 构建图形上传处理
    messages = [{"role": "system", "content": system_prompt}]
    if image_data:
        messages.append([{"role": "user", "content":
            [{"type": "text", "text": prompt},
             {"type": "image_url", "image_url": {
                 "url": f"data:image/jpeg;base64,{image_data}"}
              }]
                          }])
        return await openai_complete_if_cache(
            model=os.getenv("MODEL_V3"),
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
            prompt="",
            system_prompt="",
            history_messages=[],
            **kwargs
        )
    else:
        messages.append({'role': 'user', 'content': prompt})
        return await openai_complete_if_cache(
            model="Qwen/Qwen3-VL-8B-Instruct",
            base_url=os.getenv("BASE_URL") + "/chat/completions",
            api_key=os.getenv("API_KEY"),
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            **kwargs
        )


class ManageRAG:
    def __init__(self, parser=None):
        self.parser = parser
        self.rag = None
        self.message_list = []

    async def init_rag(self,working_dir, project):
        """初始化rag对象的函数""
        """
        self.lightrag = LightRAG(
            working_dir=working_dir,
            # max_parallel_insert=4,
            workspace=project,
            embedding_func=EmbeddingFunc(embedding_dim=4096, func=embedding_model_func),  # 配置嵌入模型处理函数
            llm_model_func=llm_model_func,  # 配置llm对话处理函数
            rerank_model_func=custom_rerank_func  # 配置重排模型处理函数
            # 修改默认的存储方式（部署线上的时候对性能有要求，知识库中的数据量特别大的情况下才需要配置）
            # 修改使用faiss来存储向量化数据
            # vector_storage = "FaissVectorDBStorage",
            # vector_db_storage_cls_kwargs = {
            #     "cosine_better_than_threshold": 0.5
            # }
        )
        # 初始化rag对象存储
        await self.lightrag.initialize_storages()
        await initialize_pipeline_status()
        """多模型处理"""
        rag = RAGAnything(lightrag=self.lightrag,  # 传递现有的 rag
                          vision_model_func=vision_model_func  # 仅需要视觉模型用于多模态处理
                          )
        self.rag = rag
        print("RAG初始化完成")
        return self.rag

    async def load_document(self, file_path):
        # 等待文档加载完成
        try:
            await self.rag.process_document_complete(
                file_path=file_path,
                output_dir=OUTPUT_PATH,
                parse_method="auto"
            )
        except Exception as e:
            print(f"文档处理失败: {e}")
            if hasattr(e, 'error_lines'):
                for line in e.error_lines:
                    print(line)
            raise

    async def delete_document(self, file_path):
        if os.path.isfile(file_path):
            doc_id = hashlib.md5(file_path.encode("utf-8")).hexdigest()
            await self.rag.adelete_by_doc_id(doc_id)
    async def search_text(self, query, mode="hybrid"):
        """知识库文本内容检索"""
        res = await self.lightrag.aquery(query,
                                         QueryParam(mode=mode,
                                                    conversation_history=self.message_list,
                                                    history_turns=10, # 上下文中加入多少条记录对话信息
                                                    stream=True)
                                        )
        result = ''
        async for chunk in res:
            result += chunk
            yield chunk
        self.message_list.append({"role": "user", "content": query})
        self.message_list.append({"role": "assistant", "content": result})
    async def multi_model_search(self, query, mode="hybrid", image_path: str = None):
        """多模态搜索"""
        multimodal_content = []
        if image_path:
            multimodal_content.append({
                "type": "image",
                "img_path": image_path
            })
        res = await self.rag.aquery_with_multimodal(query,
                                                    param=QueryParam(mode=mode, stream=True),
                                                    multimodal_content=multimodal_content)
        result = ""
        async for chunk in res:
            result += chunk
        return result
async def main():
    # 实例化rag对象
    manager_rag = ManageRAG()
    # 初始化rag对象
    rag = await manager_rag.init_rag(working_dir="./rag_storage", project="web_shop")
    # 加载文档
    await manager_rag.load_document(file_path="./document/需求说明书.md")
    # 获取文档内容
    res = manager_rag.search_text(query="获取购物车的需求文档")
    async for chunk in res:
        print(chunk, end='', flush=True)
"""
项目文档的知识库：
1、生成功能用例的（Agent）：某个需求去生成用例（完整的需求文档，业务流程图，数据库字典）
2、生成接口自动化用例（Agent）：给某个业务流生成用例（业务流的接口链）
---->完整的业务流接口用例
3、做一个项目的知识问答助手
"""
if __name__ == '__main__':
    asyncio.run(main())