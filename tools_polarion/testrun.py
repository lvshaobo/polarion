# -*- coding: UTF-8 –*-

import re
import os
from color import red, green, blue


xml_testrun_init = """<?xml version="1.0" encoding="utf-8"?>
    <testsuites>
        <properties>
            <property name="polarion-project-id" value="{}"/>
            <property name="polarion-user-id" value="{}"/>
            <property name="polarion-custom-assignee" value="{}"/>
            <property name="polarion-custom-plannedin" value="{}"/>
            <property name="polarion-include-skipped" value="{}"/>
            <property name="polarion-dry-run" value="{}"/>
            <property name="polarion-testrun-id" value="{}"/>
            <property name="polarion-testrun-type-id" value="{}"/>
        </properties>
        <testsuite errors="0" failures="0" name="pytest" skipped="0" tests="1" time="0.006">
    """

xml_testrun_end = """    </testsuite>
    </testsuites>
    """

xml_testcase_passed = """        <testcase classname="TestClass" name="test_name" time="1">
                <properties>
                    <property name="polarion-testcase-id" value="{}"/>
                </properties>
            </testcase>
    """

xml_testcase_failed = """        <testcase classname="TestClass" name="test_name" time="1">
                <failure message="failure" type="failure"/>
                <properties>
                    <property name="polarion-testcase-id" value="{}"/>
                </properties>
            </testcase>
    """


def short_model(model):
    tmp = re.split('[-_]', model)
    ans = ""
    # print(tmp)
    for x in tmp:
        # 尝试提取型号，通过以'-''_'作为分割符，寻找同时有数字和字符的字符串作为型号，过滤掉速度如10Gb
        if x.isalnum() and (not x.isalpha()) and (not x.isdigit()) and ("Gb" not in x):
            if ans == "":
                ans = x
            else:
                ans += "_" + x
    return ans


def gen_run_id_for_case(case_name, driver, model):
    """
    :param case_name:
    :param driver:
    :param model:
    :return:
    """
    #############################
    #######可能需要手动维护########
    #############################
    if "sriov" in case_name:
        componet = "_SRIOV"
    elif "macvtap" in case_name:
        componet = "_MACVTAP"
    elif "bonding/" in case_name:
        componet = "_BONDING"
    elif "team/" in case_name:
        componet = "_TEAM"
    elif "openvswitch" in case_name:
        componet = "_OVS"
    elif "vlan/" in case_name:
        componet = "_VLAN"
    elif "bridge/" in case_name:
        componet = "_BRIDGE"
    elif "nic/" in case_name:
        componet = "_NIC"
    else:
        componet = "_OTHER"
    if driver != "":
        componet += ("_" + driver)
    if model != "":
        componet += ("_" + short_model(model))
    return "{}".format(componet)


def gen_runs_ids_for_cases(cases, prefix):
    _case = cases[0].index("CASE")
    _driver = -1
    _model = -1
    if "DRIVER" in cases[0]:
        _driver = cases[0].index("DRIVER")
    if "MODEL" in cases[0]:
        _model = cases[0].index("MODEL")
        # need modify???
    runs_ids = map(
        lambda x: str(prefix) + gen_run_id_for_case(x[_case], x[_driver] if _driver != -1 else "", x[_model] if _model != -1 else ""), cases[1:]
    )
    return list(runs_ids)


def post_runs(run_ids, case_ids, case_results, case_comments, run_path, project, login, run_plannedin, dryrun):
    """post TestRun to Polarion"""
    for index, (case_id, run_id, result, comment) in enumerate(zip(case_ids, run_ids, case_results, case_comments)):
        if "%s.xml" % run_id in os.listdir(run_path):
            tr = open("{}/{}.xml".format(run_path, run_id), 'a')
        else:
            tr = open("{}/{}.xml".format(run_path, run_id), 'a')
            tr.write(xml_testrun_init.format(
                project, login, login, run_plannedin,
                "true", dryrun, run_id, "featureverification"
            ))
        if case_id is not None and result == "passed":
            tr.write(xml_testcase_passed.format(case_id))
        elif case_id is not None and result == "failed":
            tr.write(xml_testcase_failed.format(case_id))
        else:
            print(red("%s is None" % case_id))
        tr.close()
    for file_name in os.listdir(run_path):
        if file_name.endswith(".xml"):
            with open("{}/{}".format(run_path, file_name), 'a') as tr:
                tr.write(xml_testrun_end)
