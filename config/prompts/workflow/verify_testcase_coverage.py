# -- encoding: utf-8 --
# @time:    	2026/10/20 下午2:57
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["test_cases", "test_point"],
    template="""
                你是一位资深测试工程师，请根据用户下面提供的测试点和测试用例，去分析测试用例是否覆盖了所有的测试点
                   已经生成的测试用例：
                   {test_cases}
                   需要测试的测试点：
                   {test_point}
                【验证要求】：
                   1. 逐个检查每个测试点是否都有对应的测试用例
                   2. 检查边界条件和异常场景是否都有覆盖
                   3. 如果某个测试点包含多个场景，检查是否都拆分成了独立用例
                【输出要求】：
                   如果全部覆盖则直接返回：已覆盖全部测试点
                   如果没有全部覆盖则返回测试点覆盖分析报告，明确指出哪些测试点未覆盖
               """
)