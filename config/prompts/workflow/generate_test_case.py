# -- encoding: utf-8 --
# @time:    	2026/10/20 下午2:53
# @Author: 		JsonLiu
# @Email:  		492224300@qq.com
existing_cases_template_str = """
                      你是一位资深测试工程师，当前已经有一批测试用例，但覆盖率分析显示仍有未覆盖的测试点。
                      请【仅针对未覆盖的测试点】补充生成新的测试用例，不要重复已有的用例。
                      已有的测试用例（不要重复生成）：
                          {existing_cases}
                      覆盖率分析报告（标明了哪些测试点未被覆盖）：
                          {coverage_report}
                      所有测试点：
                          {test_point}
                      输出的用例，包含测试用例的八要素：
                          用例编号(case_id)、用例名称(case_name)、优先级(priority) 
                          前置步骤(preconditions)、测试步骤(test_steps) 
                          输入数据(test_data)、预期结果(expected_result)、实际结果(actual_result)
                      要以json格式输出：
                         [
                              {{{{
                                  "case_id": "TEST_001",
                                  "case_name": "用例名称",
                                  "priority": "优先级",
                                  "preconditions": "前置步骤",
                                  "test_steps": "测试步骤",
                                  "test_data": "输入数据",
                                  "expected_result": "预期结果",
                                  "actual_result": "实际结果"
                              }}}},
                              ...
                          ]
                        【重要输出要求】：
                            1. 直接输出纯JSON数组，不要添加任何markdown标记
                            2. 不要添加任何注释或解释性文字，只输出JSON
                            3. actual_result字段填写空字符串
                            4. 只生成未覆盖测试点对应用例，不要重复已有用例
                            5. case_id 必须以 TEST_ 前缀加三位数字递增格式，例如：TEST_001、TEST_002、TEST_003...，不要使用功能编号（如F3.1_01）
                            6. priority 填写高、中、低
                   """
template_str =  """
                      你是一位资深测试工程师，请基于下面的测试点生成标准的测试用例。
                       输入测试点：
                           {test_point}
                      输出的用例，包含测试用例的八要素：
                          用例编号(case_id)、用例名称(case_name)、优先级(priority) 
                          前置步骤(preconditions)、测试步骤(test_steps) 
                          输入数据(test_data)、预期结果(expected_result)、实际结果(actual_result)
                      要以json格式输出：
                         [
                              {{{{
                                  "case_id": "TEST_001",
                                  "case_name": "用例名称",
                                  "priority": "优先级", 
                                  "preconditions": "前置步骤",
                                  "test_steps": "测试步骤",
                                  "test_data": "输入数据",
                                  "expected_result": "预期结果",
                                  "actual_result": "实际结果"
                              }}}},
                              ...
                          ]
                      【重要输出要求】：
                          1. 直接输出纯JSON数组，不要添加任何markdown标记
                          2. 不要添加任何注释或解释性文字，只输出JSON
                          3. actual_result字段填写空字符串
                          4. case_id 必须以 TEST_ 前缀加三位数字递增格式，例如：TEST_001、TEST_002、TEST_003...，不要使用功能编号（如F3.1_01）
                          5. priority 填写高、中、低
                   """
