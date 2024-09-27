import aiohttp
import asyncio
import random
import json
from datetime import datetime
from . import *

class GameSession:
    def __init__(self, acc_data, tgt_score, prxy=None):
        self.b_url = "https://tonclayton.fun"
        self.s_id = None
        self.a_data = acc_data
        self.hdrs = get_headers(self.a_data)
        self.c_score = 0
        self.t_score = tgt_score
        self.inc = 10
        self.pxy = prxy

        self.pxy_dict = {
            'http': f'http://{self.pxy}' if self.pxy else None,
            'https': f'http://{self.pxy}' if self.pxy else None,
        }

    @staticmethod
    def fmt_ts(ts):
        dt = datetime.fromisoformat(ts[:-1])
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    async def lg(self, session):
        url = f"{self.b_url}/api/user/login"
        async with session.post(url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
            if resp.status == 200:
                usr_data = await resp.json()
                usr = usr_data.get('user', {})
                log(hju + f"Proxy: {pth}{self.pxy or 'No proxy used'}")
                log(htm + "~" * 38)
                log(bru + f"Username: {pth}{usr.get('username', 'N/A')}")
                log(hju + f"Points: {pth}{usr.get('tokens', 'N/A'):,.0f} {hju}| XP: {pth}{usr.get('current_xp', 'N/A')} {hju}| Level: {pth}{usr.get('level', 'N/A')}")
            else:
                log(mrh + f"Login failed: {await resp.text()}")

    async def chk_and_clm_daily(self, session):
        st_url = f"{self.b_url}/api/user/daily-reward-status"
        cl_url = f"{self.b_url}/api/user/daily-claim"

        async with session.post(st_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
            if resp.status == 200:
                st_data = await resp.json()
                can_clm = st_data.get("can_claim", False)
                curr_day = st_data.get("current_day", None)
                log(hju + f"Current Streak Day: {pth}{curr_day} Days")

                if can_clm:
                    async with session.post(cl_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as cl_resp:
                        if cl_resp.status == 200:
                            cl_data = await cl_resp.json()
                            log(cl_data.get(kng + f"message", hju + f"Daily reward claimed successfully."))
                        elif "user is not" in await cl_resp.text():
                            log(mrh + f"Claim failed: Please subscribed to {pth}@clayton")
                        else:
                            log(mrh + f"Claim failed: {await cl_resp.text()}")
                else:
                    log(kng + f"You have already checked in today!")
            else:
                log(mrh + f"Status check failed: {await resp.text()}")

    async def mng_rwd_and_strt_mn(self, session):
        lg_url = f"{self.b_url}/api/user/login"
        
        try:
            async with session.post(lg_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
                if resp.status != 200:
                    log(mrh + f"Login check failed: {await resp.text()}")
                    return

                lg_data = await resp.json()
                can_claim = lg_data['user']['can_claim']
                act_farm = lg_data['user']['active_farm']
        except Exception as e:
            log(mrh + f"An error occurred while checking login: {e}")
            return

        # Claim rewards if available
        if can_claim:
            await self._clm_rwd(session)
            
            # Recheck login after claiming rewards
            try:
                async with session.post(lg_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
                    if resp.status != 200:
                        log(mrh + f"Login check failed after claiming rewards: {await resp.text()}")
                        return

                    lg_data = await resp.json()
                    act_farm = lg_data['user']['active_farm']
            except Exception as e:
                log(mrh + f"An error occurred while rechecking login: {e}")
                return

        # Start farming if not active
        if not act_farm:
            await self._strt_mn(session)
        else:
            log(hju + f"Mining session is currently active.")

    async def _clm_rwd(self, session):
        cl_url = f"{self.b_url}/api/user/claim"
        try:
            async with session.post(cl_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
                if resp.status == 200:
                    rwd = await resp.json()
                    log(hju + f"Claimed mining: {pth}{rwd['xp_earned']} {hju} XP| Total tokens: {pth}{rwd['tokens']}")
                elif "storage is not filled" in await resp.text():
                    log(bru + f"Mining storage is not filled")
                else:
                    log(mrh + f"Claim failed: {htm}{await resp.text()}")
        except Exception as e:
            log(mrh + f"An error occurred while claiming rewards: {htm}{e}")

    async def _strt_mn(self, session):
        st_url = f"{self.b_url}/api/user/start"
        try:
            async with session.post(st_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
                if resp.status == 200:
                    st_time = await resp.json()
                    fmt_time = self.fmt_ts(st_time['start_time'])
                    log(hju + f"Mining started successfully")
                    log(kng + f"Mining will end at {pth}{fmt_time} ")
                else:
                    log(mrh + f"Mining start failed: {htm}{await resp.text()}")
        except Exception as e:
            log(mrh + f"An error occurred while starting mining: {htm}{e}")

    async def run_g(self, session):
        with open('config.json', 'r') as cf:
            cfg = json.load(cf)
        
        g_tickets = cfg.get("game_ticket_to_play", 1)

        for ticket in range(g_tickets):
            log(hju + f"Try to {bru}play game {hju}with ticket {pth}{ticket + 1}/{g_tickets}")

            st_url = f"{self.b_url}/api/stack/start"
            async with session.post(st_url, headers=self.hdrs, json=None, proxy=self.pxy_dict['http']) as resp:
                if resp.status == 200:
                    self.s_id = (await resp.json()).get("session_id")
                    log(bru + f"Play game: {hju}started{pth} {self.s_id}")
                elif "no daily attempts left" in await resp.text():
                    log(kng + f"Play game: ticket attempts are over")
                    return
                else:
                    log(mrh + f"Play game: failed {await resp.text()}")
                    return

            self.c_score = 0

            while self.c_score < self.t_score:
                self.c_score += self.inc
                up_url = f"{self.b_url}/api/stack/update"
                async with session.post(up_url, headers=self.hdrs, json={"score": self.c_score}, proxy=self.pxy_dict['http']) as resp:
                    if resp.status == 200:
                        log(bru + f"Play game: {hju}score updated: {pth}{self.c_score}")
                    else:
                        log(mrh + f"Play game: score update failed!")

                await countdown_timer(random.randint(4, 6))

            en_url = f"{self.b_url}/api/stack/end"
            async with session.post(en_url, headers=self.hdrs, json={"score": self.c_score}, proxy=self.pxy_dict['http']) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    log(hju + f"Result XP: {pth}{res['xp_earned']} {hju}| Points: {pth}{res['earn']}")
                    log(hju + f"Current XP Total: {pth}{res['current_xp']} XP")
                    await countdown_timer(3)
                else:
                    log(mrh + f"End session failed: {htm}{await resp.text()}")

    async def cpl_and_clm_tsk(self, session, tsk_type='daily'):
        if tsk_type == 'daily':
            t_url = f"{self.b_url}/api/user/daily-tasks"
            cmp_url_tpl = f"{self.b_url}/api/user/daily-task/{{task_id}}/complete"
            clm_url_tpl = f"{self.b_url}/api/user/daily-task/{{task_id}}/claim"
        else:
            t_url = f"{self.b_url}/api/user/partner/get"
            cmp_url_tpl = f"{self.b_url}/api/user/partner/complete/{{task_id}}"
            clm_url_tpl = f"{self.b_url}/api/user/partner/reward/{{task_id}}"

        await countdown_timer(random.randint(1, 2))
        
        for attempt in range(3):
            async with session.post(t_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
                if resp.status == 200:
                    tasks = await resp.json()
                    break 
                else:
                    log(mrh + f"Failed to retrieve {pth}{tsk_type} {mrh}tasks (Attempt {attempt + 1})")
                    await asyncio.sleep(1)
                    if attempt == 2: 
                        return 

        for t in tasks:
            t_id = t['id'] if tsk_type == 'daily' else t['task_id']
            if not t.get('is_completed', False):
                cmp_url = cmp_url_tpl.format(task_id=t_id)
                async with session.post(cmp_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as cmp_resp:
                    if cmp_resp.status == 200:
                        log(hju + f"Completed {pth}{tsk_type}{hju} task: {pth}{t.get('task_type', t.get('task_name'))}")
                        await asyncio.sleep(random.uniform(1, 3))
                        clm_url = clm_url_tpl.format(task_id=t_id)
                        async with session.post(clm_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as clm_resp:
                            if clm_resp.status == 200:
                                clm_data = await clm_resp.json()
                                log(hju + f"Claimed {pth}{t.get('task_type', t.get('task_name'))} {hju}Successfully | Reward: {pth}{clm_data.get('reward', '250')}")
                                await asyncio.sleep(random.uniform(1, 3))
                            else:
                                log(mrh + f"Failed to claim reward for task {pth}{t_id}")
                    else:
                        log(mrh + f"Failed to complete task {pth}{t_id}: {htm}{await cmp_resp.text()}")
            else:
                log(hju + f"{tsk_type.capitalize()} {kng}task {pth}{t.get('task_type', t.get('task_name'))} {kng}already completed.")

    async def clm_tsk_bot(self, session):
        cl_url = f"{self.b_url}/api/user/task-bot-claim"
        
        try:
            async with session.post(cl_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": await resp.text()}
        except Exception as e:
            return {"exception": str(e)}

    async def clm_all_achv(self, session):
        ach_url = f"{self.b_url}/api/user/achievements/get"
        
        try:
            async with session.post(ach_url, headers=self.hdrs, json={}, proxy=self.pxy_dict['http']) as resp:
                if resp.status != 200:
                    log(mrh + f"Failed to retrieve achievements")
                    return

                ach_data = await resp.json()
        except Exception as e:
            log(mrh + f"An error occurred while retrieving achievements: {e}")
            return

        ach_types = ['friends', 'games', 'stars', 'ton']
        for a_type in ach_types:
            for ach in ach_data.get(a_type, []):
                if ach['is_completed'] and not ach['is_rewarded']:
                    await self._clm_achv(session, a_type, ach['level'])

    async def _clm_achv(self, session, a_type, lvl):
        cl_url = f"{self.b_url}/api/user/achievements/claim"
        pl = {"type": a_type, "level": lvl}

        try:
            async with session.post(cl_url, headers=self.hdrs, json=pl, proxy=self.pxy_dict['http']) as resp:
                if resp.status == 200:
                    rwd_data = await resp.json()
                    log(hju + f"Achievement {pth}{a_type} {hju}level {pth}{lvl}{hju}: Reward {pth}{rwd_data['reward']}")
                else:
                    log(mrh + f"Failed to claim {pth}{a_type} {mrh}achievement for level {pth}{lvl}")
        except Exception as e:
            log(mrh + f"An error occurred while claiming achievement: {htm}{e}")

async def clm_with_dly(session, g_session, dly=1):
    await asyncio.sleep(dly)
    await g_session.clm_all_achv(session)

async def ld_accs(fp):
    with open(fp, 'r') as file:
        return [line.strip() for line in file.readlines()]

async def ld_prx(fp):
    with open(fp, 'r') as file:
        return [line.strip() for line in file.readlines()]

async def main():
    cfg = read_config()
    tgt_score = random.randint(79, 93)
    use_prxy = cfg.get('use_proxy', False)
    ply_game = cfg.get('play_game', False)
    cpl_tsk = cfg.get('complete_task', False)
    acc_dly = cfg.get('account_delay', 5)
    cntdwn_loop = cfg.get('countdown_loop', 3800)
    
    prx = await ld_prx('proxies.txt') if use_prxy else []
    accs = await ld_accs("data.txt")

    async with aiohttp.ClientSession() as session:
        for idx, acc in enumerate(accs, start=1):
            log(hju + f"Processing account {pth}{idx} {hju}of {pth}{len(accs)}")
            prxy = prx[idx % len(prx)] if use_prxy and prx else None
            game = GameSession(acc, tgt_score, prxy)

            await game.lg(session)
            await game.chk_and_clm_daily(session)
            await game.mng_rwd_and_strt_mn(session)
            if ply_game:
                await game.run_g(session)
            if cpl_tsk:
                await game.cpl_and_clm_tsk(session, tsk_type='daily')
                await game.cpl_and_clm_tsk(session, tsk_type='partner')
                await game.clm_tsk_bot(session)
            await clm_with_dly(session, game, dly=1)

            log_line()
            await countdown_timer(acc_dly)

        await countdown_timer(cntdwn_loop)
