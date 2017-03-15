# -*- coding: UTF-8 –*- 

from __future__ import print_function

__version__ = '0.2'
__author__ = 'Shaobo Lv'

import time
from log import Logger
from color import red, green
from suds import WebFault
from pylarion.work_item import _WorkItem, TestCase
from pylarion.exceptions import PylarionLibException

logger = Logger(__name__)


def get_case_id_by_sql(prefix, case_name, topo, project):
    case_name = case_name.strip()
    topo = topo.strip()
    rs = []
    sql = (
        "SELECT WORKITEM.C_URI FROM WORKITEM "
        "INNER JOIN PROJECT on PROJECT.C_URI = WORKITEM.FK_URI_PROJECT "
        "WHERE WORKITEM.C_TYPE = 'testcase' AND "
        "WORKITEM.C_TITLE like '%s%%%s%%%s' AND "
        "PROJECT.C_ID = '%s'"
    )
    statement = sql % (prefix, case_name, topo, project)
    try:
        items = _WorkItem.query(statement, True, fields=["work_item_id", "title"])
    except:
        print("retry")
        time.sleep(2)
        return get_case_id_by_sql(prefix, case_name, topo, project)
    else:
        rs.extend(items)
        return rs


def create_new_case(prefix, case_name, topo, document, project):
    """create new case through the name and topo of case"""
    print(green("Create New Testcase NAME:%s, TOPO:%s" % (case_name, topo)))
    if topo == "":
        case_title = "{}: {}".format(prefix, case_name)
    else:
        case_title = "{}: {} FUNC={}".format(prefix, case_name, topo)
    try:
        case_item = TestCase.create(
                        project,
                        title=case_title,
                        desc="",
                        caseimportance="high",
                        caseautomation="automated",
                        caseposneg="positive",
                        caselevel="component",
                        testtype="functional",
                        subtype1="-"
        )
        document.move_work_item_here(case_item.work_item_id, None)
    except:
        return create_new_case(prefix, case_name, topo, document, project)
    return case_item.work_item_id


def get_case_id(case_title_prefix, case_name, topo, document, project, dryrun):
    """get or create case_id"""
    case_name = case_name.replace("/kernel/networking/", "")
    try:
        if topo == "":
            case_list = get_case_id_by_sql(case_title_prefix, case_name, topo, project)
        else:
            tmp1 = get_case_id_by_sql(case_title_prefix, case_name, "TOPO=%s" % topo, project)
            tmp2 = get_case_id_by_sql(case_title_prefix, case_name, "FUNC=%s" % topo, project)
            case_list = tmp1 + tmp2
    except WebFault:
        # retry
        time.sleep(3)
        return get_case_id(case_title_prefix, case_name, topo, document, project, dryrun)
    except PylarionLibException:
        # retry
        time.sleep(3)
        return get_case_id(case_title_prefix, case_name, topo, document, project, dryrun)
    if len(case_list) == 1:
        logger.debug("There is only one %s" % case_list[0].work_item_id)
        return case_list[0].work_item_id
    elif len(case_list) == 0:
        logger.warning("Can't find right case-NAME: {}, TOPO: {}".format(case_name, topo))
        if not dryrun:
            try:
                # logger.info("%s can't be found" % case_name)
                return create_new_case(case_title_prefix, case_name, topo, document, project)
            except:
                logger.error("Can't create new test case automatically.")
                raise
    else:
        # 找到多个，通过“TOPO=” 或者“--FUNC=”过滤case
        logger.error("Find more than one case. \"{}\", \"{}\".".format(case_name, topo))
        print(red("Find more than one case. \"{}\", \"{}\".".format(case_name, topo)))
        with open("fail.csv", "a") as fcsv:
            fcsv.write("Error: Find more than one case-----\n")
            fcsv.write(time.ctime() + "\n")
            fcsv.write("{},{}\n".format(case_name, topo))
        return None


def get_cases_ids(cases, case_title_prefix, document, project, dryrun):
    _case = cases[0].index("CASE")
    _topo = cases[0].index("TOPO")
    cases_ids = [0 for i in cases]
    dic_ = {}
    for i, x in enumerate(cases[1:]):
        x_tuple = (x[_case], x[_topo])
        # print('The %s-th case' % str(i + 2))
        if x_tuple not in dic_:
            dic_[x_tuple] = get_case_id(case_title_prefix, x[_case], x[_topo], document, project, dryrun)
        cases_ids[i] = dic_[x_tuple]
    return cases_ids

def get_cases_roles(cases):
    _role = cases[0].index("ROLE")
    return list(map(lambda x: x[_role], cases[1:]))


def get_cases_results(cases):
    # Beaker result or final result is pass, it is pass.
    _res = cases[0].index("Beaker RESULT")
    _fres = cases[0].index("Final RESULT")

    def get_case_result(res, fres):
        if res.upper() == "PASS" or fres.upper() == "PASS":
            return "passed"
        else:
            return "failed"
    res_vec = list(map(lambda x: get_case_result(x[_res], x[_fres]), cases[1:]))
    return res_vec


def get_cases_comments(cases):
    _bz = -1
    _cm = cases[0].index("COMMENT")
    if "BZ" in cases[0]:
        _bz = cases[0].index("BZ")

    def get_case_comment(cm, bz):
        return cm + ("\tBZ: " + bz) if len(bz) else ""

    return list(map(lambda x: get_case_comment(x[_cm], x[_bz] if _bz != -1 else ""), cases[1:]))


def cases_filter(cases):
    """delete case which ends with 'dmesg'"""
    _case = cases[0].index("CASE")
    _topo = cases[0].index("TOPO")
    for index, case in enumerate(cases):
        if case[_topo].endswith(('dmesg', '/')):
            del cases[index]
    return cases

"""
def cases_filter(cases, cf=list()):
    _case = cases[0].index("CASE")
    return [cases[0]] + [x for x in cases[1:] if x[_case] not in cf]
"""
