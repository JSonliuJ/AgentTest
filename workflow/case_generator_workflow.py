# -- encoding: utf-8 --
# @time:    	2026/10/17 下午6:20
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
# -- encoding: utf-8 --
# @time:    	2026/10/10 下午12:49
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
"""
1、主工作流
    1、用户输入需求文档
    2、分析出所有的测试点子工作流：（基于需求整理测试点--->验证测试点覆盖率--->对于未覆盖的测试点补全--->输出所有的测试点）
    3、基于上一个节点生成的测试点生成特点格式的测试用例
父子图(工作流）需要共亭的数据：
    1、需求文档
    2、生成的测试点
"""
import asyncio
import json
import operator
import random
from typing import TypedDict, List, Annotated
from langchain_core.output_parsers import JsonOutputParser
from langgraph.config import get_stream_writer
from langgraph.types import Command
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph,START,END
from pydantic import BaseModel
from AgentTest.config.prompts.workflow import generate_test_points
from AgentTest.config.prompts.workflow import verify_test_points_coverage
from AgentTest.config.prompts.workflow import generate_test_case
from AgentTest.config.prompts.workflow import verify_testcase_coverage
from AgentTest.config.settings import llm


class ParentState(TypedDict):
    """主工作流的状态"""
    # 输入需求文档
    query: str
    input_requirement: str
    test_point: str
    test_cases: list
    # 测试用例覆盖率的报告分析
    test_case_coverage_report: str


class SubState(TypedDict):
    """子工作流的状态"""
    # 输入需求文档
    input_requirement: str
    # 生成的测试点
    # test_point: Annotated[list, operator.add]
    test_point: list
    # 覆盖率分析报告
    coverage_report: str

class TestCaseModel(BaseModel):
    """测试用例数据模型"""
    case_id: str
    case_name: str
    priority: str
    preconditions: str
    test_steps: str
    test_data: str
    expected_result: str
    actual_result: str | None

class TestPointModel(BaseModel):
    type: str
    test_point: str
class GenerateTestPointWorkflow:
    # =========================子工作流的实现=========================
    # 基于需求整理测试点 节点
    def generate_test_points(self,state: SubState):
        """基于需求文档生成测试点"""
        writer = get_stream_writer()
        writer("【开始执行节点】：基于需求文档生成测试点")
        # 获取用户输入的文档
        input_requirement = state.get("input_requirement")
        parser = JsonOutputParser(pydantic_schema=List[TestPointModel])
        # 编写提示词
        chain = generate_test_points.prompt | llm | parser
        # 调用大模型进行生成
        response = chain.invoke({"document": input_requirement})
        # 获取大模型调用的结果
        return {"test_point": response}


    # 验证测试点覆盖率 节点
    def verify_test_points_coverage(self,state: SubState):
        """验证测试点的覆盖率"""
        writer = get_stream_writer()
        writer("【开始执行节点】：验证测试点的覆盖率")
        chain = verify_test_points_coverage.prompt | llm
        # 调用大模型进行生成
        response = chain.invoke({
            "test_point": state.get("test_point"),
            "document": state.get("input_requirement")
        })
        coverage_report = response.content
        # 获取大模型调用的结果
        return {"coverage_report": coverage_report}

    # 输出所有的测试点
    def output_all_test_points(self,state: SubState):
        """输出所有的测试点"""
        writer = get_stream_writer()
        writer("【开始执行节点】：输出所有的测试点")
        return {"test_point": state.get("test_point")}


    # 路由分发的节点
    def route_dispatch(self,state: SubState):
        """路由分派"""
        writer = get_stream_writer()
        writer("【开始执行节点】：根据测试点的覆盖情况进行路由分发")
        if "测试点已经全部覆盖" in state["coverage_report"]:
            return "输出所有测试点"
        else:
            return "生成测试点"

    def sub_workflow(self):
        # 对子节点进行编排
        workflow = StateGraph(SubState)
        # 添加工作流的节点
        workflow.add_node("生成测试点", self.generate_test_points)
        workflow.add_node("验证测试点覆盖率", self.verify_test_points_coverage)
        workflow.add_node("路由分派", self.route_dispatch)
        workflow.add_node("输出所有测试点", self.output_all_test_points)
        # 对节点进行编排
        workflow.add_edge(START, "生成测试点")
        workflow.add_edge("生成测试点", "验证测试点覆盖率")
        workflow.add_conditional_edges("验证测试点覆盖率", self.route_dispatch, ["生成测试点", "输出所有测试点"])
        workflow.add_edge("输出所有测试点", END)
        # 对节点进行编译(作为子工作流使用，配置checkpointer=True即可开启子图的检查点)
        graph1 = workflow.compile()
        return graph1

class GenerateTestCaseWorkflow:
    # ================================主工作流的开发================================
    # 生成测试用例的节点
    def generate_test_case(self,state: ParentState):
        """基于测试点生成特定格式的测试用例"""
        writer = get_stream_writer()
        writer("【开始执行节点】：基于测试点生成特定格式的测试用例")
        test_point = state.get("test_point")
        print(f"\n生成的测试点：\n{json.dumps(test_point, ensure_ascii=False, default=str, indent=2)}\n", flush=True)
        writer(f"\n生成的测试点：\n{json.dumps(test_point, ensure_ascii=False, default=str, indent=2)}\n")
        existing_cases = state.get("test_cases") or []
        coverage_report = state.get("test_case_coverage_report") or ""
        if existing_cases:
            template_str = generate_test_case.existing_cases_template_str
        else:
            template_str = generate_test_case.template_str
        prompt = PromptTemplate(
            input_variables=["test_point"],
            template=template_str
        )
        parser = JsonOutputParser(pydantic_schema=List[TestCaseModel])
        chain = prompt | llm | parser
        input_vars = {"test_point": state.get("test_point")}
        if existing_cases:
            input_vars["existing_cases"] = str(existing_cases)
            input_vars["coverage_report"] = coverage_report
        response = chain.invoke(input_vars)
        # 后处理：强制重新编号 case_id 为 TEST_001 递增格式
        start_index = len(existing_cases) + 1 if existing_cases else 1
        for idx, case in enumerate(response, start=start_index):
            case["case_id"] = f"TEST_{idx:03d}"
        if existing_cases:
            merged = existing_cases + response
            writer(f"\n【补充生成】新增 {len(response)} 条用例，累计 {len(merged)} 条")
            return {"test_cases": merged}
        else:
            writer(f"\n【首次生成】生成 {len(response)} 条用例")
            return {"test_cases": response}
    # 分析测试用例是否覆盖所有的测试点
    def verify_testcase_coverage(self,state: ParentState):
        """验证测试用例的覆盖率"""
        writer = get_stream_writer()
        writer("【开始执行节点】：开始验证用例覆盖率")
        chain = verify_testcase_coverage.prompt | llm
        response = chain.invoke({
            "test_cases": state.get("test_cases"),
            "test_point": state.get("test_point")
        })
        result = response.content
        if "已覆盖全部测试点" in result:
            return Command(goto="保存测试用例")
        else:
            # 再次补充生成测试用例
            return Command(goto="生成测试用例", update={"test_case_coverage_report": result})


    def save_test_cases(self,state: ParentState):
        """保存测试用例"""
        writer = get_stream_writer()
        writer("【开始执行节点】：保存测试用例")
        test_cases = state.get("test_cases")
        # 只输出JSON格式，不输出其他内容
        writer(f"\n共生成 {len(test_cases)} 条测试用例")
        writer(f"\n\n测试用例数据（JSON格式）：")
        writer(f"\n{json.dumps(test_cases, ensure_ascii=False, indent=2)}")
        return {"test_cases": test_cases}

    def main_workflow(self):
        """定义主工作流"""
        graph1 = GenerateTestPointWorkflow().sub_workflow()
        main_workflow = StateGraph(ParentState)
        # 把子工作流添加到主工作流中的一个节点
        main_workflow.add_node("生成测试点", graph1)
        main_workflow.add_node("生成测试用例", self.generate_test_case)
        main_workflow.add_node("验证测试用例覆盖率", self.verify_testcase_coverage)
        main_workflow.add_node("保存测试用例", self.save_test_cases)

        # 对节点进行编排序
        main_workflow.add_edge(START,"生成测试点")
        main_workflow.add_edge("生成测试点", "生成测试用例")
        main_workflow.add_edge("生成测试用例", "验证测试用例覆盖率")
        main_workflow.add_edge("保存测试用例", END)
        # 对主工作流进行编译,设置检查点
        main_workflow = main_workflow.compile()
        return main_workflow

if __name__ == '__main__':
    pass
