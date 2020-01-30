from app.spiders.luogu_spider import LuoguSpider
from app.test_base import client


def test_luogu_user_info(client):
    from app.models.oj_username import OJUsername
    oj_username = OJUsername()

    # uid
    oj_username.oj_username = '62916'
    accept_problems = {}
    res = LuoguSpider.get_user_info(oj_username, accept_problems)
    f = 0
    for i in res['data']:
        if i['oj'] == 'luogu' and i['problem_pid'] == '1001' and i['accept_time'] is None:
            f = 1
            break
    assert f

    # 用户名
    oj_username.oj_username = 'taoting'
    accept_problems = {}
    res = LuoguSpider.get_user_info(oj_username, accept_problems)
    f = 0
    for i in res['data']:
        if i['oj'] == 'luogu' and i['problem_pid'] == '1001' and i['accept_time'] is None:
            f = 1
            break
    assert f


def test_luogu_problem_info(client):
    assert LuoguSpider.get_problem_info('1001')['rating'] == 1500
