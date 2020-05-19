import datetime

from app.config.setting import DEFAULT_PROBLEM_RATING
from app.libs.helper import str_to_datetime
from app.models.accept_problem import AcceptProblem
from app.models.oj import OJ
from app.models.oj_username import OJUsername
from app.models.problem import Problem
from app.models.user import User
from app.spiders.base_spider import BaseSpider
# 导入spider
from app.spiders.codeforces_spider import CodeforcesSpider
from app.spiders.hdu_spider import HduSpider
from app.spiders.hysbz_spider import HysbzSpider
from app.spiders.jisuanke_spider import JisuankeSpider
from app.spiders.loj_spider import LojSpider
from app.spiders.luogu_spider import LuoguSpider
from app.spiders.nowcoder_spider import NowcoderSpider
from app.spiders.pintia_spider import PintiaSpider
from app.spiders.poj_spider import PojSpider
from app.spiders.vjudge_spider import VjudgeSpider
from app.spiders.zucc_spider import ZuccSpider


def task_crawl_accept_problem(username=None, oj_id=None):
    from tasks import task_f, task_single_f
    if username:
        user_list = [User.get_by_id(username)]
    else:
        user_list = User.search(status=1, page_size=1000)['data']
    if oj_id:
        oj_id_list = [OJ.get_by_id(oj_id)]
    else:
        oj_id_list = OJ.search(status=1, page_size=100)['data']

    for user in user_list:
        for oj in oj_id_list:
            if oj.name in ['pintia', 'luogu']:
                task_single_f.delay(crawl_accept_problem, username=user.username, oj_id=oj.id)
            else:
                task_f.delay(crawl_accept_problem, username=user.username, oj_id=oj.id)


def crawl_accept_problem(username, oj_id):
    user = User.get_by_id(username)
    if not user:
        return
    oj = OJ.get_by_id(oj_id)
    if not oj:
        return
    oj_username = OJUsername.search(username=username, oj_id=oj_id)['data']
    if not oj_username:
        return

    oj_username = oj_username[0]
    oj_spider: BaseSpider = globals()[oj.name.title() + 'Spider']()

    accept_problems = dict()

    for i in AcceptProblem.search(username=username, page_size=10000)['data']:
        accept_problems["{}-{}".format(i.problem.oj.name, i.problem.problem_pid)] = \
            datetime.datetime.strftime(i.create_time, '%Y-%m-%d %H:%M:%S')

    res = oj_spider.get_user_info(oj_username, accept_problems.copy())
    if res['success']:
        oj_username.modify(last_success_time=datetime.datetime.now())
    crawl_accept_problems = res['data']
    print(crawl_accept_problems)

    deduplication_accept_problem = list()

    for i in crawl_accept_problems:
        pid = "{}-{}".format(i['oj'], i['problem_pid'])
        if i['accept_time'] is not None:
            if accept_problems.get(pid):
                if i['accept_time'] < accept_problems.get(pid):
                    deduplication_accept_problem.append(i)
            else:
                deduplication_accept_problem.append(i)
        else:
            if accept_problems.get(pid) is None:
                deduplication_accept_problem.append(i)

    print(len(deduplication_accept_problem))
    for i in deduplication_accept_problem:
        oj = OJ.get_by_name(i['oj'])
        problem = Problem.get_by_oj_id_and_problem_pid(oj.id, i['problem_pid'])
        task_crawl_problem_rating(problem.id)
        accept_problem = AcceptProblem.get_by_username_and_problem_id(username, problem.id)
        accept_problem.modify(create_time=str_to_datetime(i['accept_time']), referer_oj_id=oj_id)


def task_crawl_problem_rating(problem_id):
    from tasks import task_f
    task_f.delay(crawl_problem_rating, problem_id=problem_id)


def crawl_problem_rating(problem_id):
    problem = Problem.get_by_id(problem_id)
    oj = OJ.get_by_id(problem.oj_id)
    try:
        oj_spider: BaseSpider = globals()[oj.name.title() + 'Spider']()
        rating = oj_spider.get_problem_info(problem.problem_pid)['rating']
    except:
        rating = DEFAULT_PROBLEM_RATING

    problem.modify(rating=rating)
