# -- encoding: utf-8 --
# @time:    	2026/10/20 下午2:50
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
            input_variables=["test_point", "document"],
            template="""
                你是一位资深的软件测试工程师，请根据提供原始的需求文档和测试点，去分析
                原始功能文档：
                {document}
                测试点：
                {test_point}
                如果测试点覆盖了需求中所有的功能，则直接回复：测试点已经全部覆盖
                如果没有全部覆盖，请给出覆盖率分析报告
            """)