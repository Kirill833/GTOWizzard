import os
from json import JSONDecodeError

import requests
import json
import pickle
import time
from loguru import logger

class Parser:

    TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjU0NTI4MDM1LCJpYXQiOjE2NTQ1MDI1MzgsImp0aSI6Ijk0YTUzN2UzNzUyYTQ1ZjM4YzFlZmU4NzY2NjUwNDY3IiwicHVibGljX2lkIjoiYWNjX3g1ZzVoOTYxdmwiLCJlbWFpbCI6ImZlcm1hdG9wNTAwQGdtYWlsLmNvbSJ9.PjKzrt8LMNPpH6b7CmVGW8KZ8DZvwrTeIUIM8gXivx8"
    PICKLE_PATH = "/Users/kirill/PycharmProjects/GTOWizzard/state.pickle"
    DATA_PATH = "/Users/kirill/PycharmProjects/GTOWizzard/data"
    CHILDREN_DATA_PATH = "/Users/kirill/PycharmProjects/GTOWizzard/children"
    state = []

    start_flag = True

    def get_solution(self, actions: str) -> dict:
        header = {
            "referer": f"https://app.gtowizard.com/solutions?gametype=Cash6m50zGeneral&depth=100&history_spot=3&preflop_actions={actions}",
            "Authorization": f"Bearer {self.TOKEN}",
            "accept": "application/json, text/plain, */*",
            "origin": "https://app.gtowizard.com",
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            "accept-Encoding": "gzip, deflate, br",
            "connection": "keep-alive",
            "host": "gtowizard.com",
            "accept-language": "ru"
        }
        url = f'https://gtowizard.com/api/v1/poker/solution/?gametype=StraddleAnteGeneral&depth=100&stacks=&preflop_actions={actions}&flop_actions=&turn_actions=&river_actions=&board=&cache_change=2022-04-08T00%3A00Z'
        _request = requests.get(url, headers=header)
        if _request.status_code == 401:
            raise Exception(401)
        return _request.json()

    def get_next_actions(self, actions: str):
        if actions + ".json" in os.listdir(self.CHILDREN_DATA_PATH):
            with open(self.CHILDREN_DATA_PATH + "/" + actions + ".json", "r") as file:
                return json.load(file)

        header = {
            "referer": f"https://app.gtowizard.com/solutions?gametype=StraddleAnteGeneral&depth=100&history_spot=2&preflop_actions={actions}",
            "Authorization": f"Bearer {self.TOKEN}",
            "accept": "application/json, text/plain, */*",
            "origin": "https://app.gtowizard.com",
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            "accept-Encoding": "gzip, deflate, br",
            "connection": "keep-alive",
            "host": "gtowizard.com",
            "accept-language": "ru"
        }
        url = f'https://gtowizard.com/api/v1/poker/next-actions/?gametype=StraddleAnteGeneral&depth=100&stacks=&preflop_actions={actions}&flop_actions=&turn_actions=&river_actions=&cache_change=2022-04-08T00%3A00Z'
        _request = requests.get(url, headers=header)
        if _request.status_code == 401:
            raise 401
        return _request.json()

    def save_solution_json(self, actions: str, json_data: dict):
        with open(f"{self.DATA_PATH}/{actions}.json", "w") as outfile:
            # outfile.write(json_data)
            json.dump(json_data, outfile)

    def save_children_json(self, actions: str, json_data: dict):
        with open(f"{self.CHILDREN_DATA_PATH}/{actions}.json", "w") as outfile:
            # outfile.write(json_data)
            json.dump(json_data, outfile)

    @staticmethod
    def beautiful_sizing(sizing_str: str) -> str:
        sizing = float(sizing_str)
        if sizing - int(sizing) < 0.01:
            return str(int(sizing))
        elif sizing_str.endswith("0"):
            return sizing_str[:-1]
        else:
            return sizing_str

    def get_action_list(self, next_actions: dict) -> list:
        actions_data = next_actions["next_actions"]["available_actions"]
        actions = [action["code"] + (self.beautiful_sizing(action["betsize"]) if action["code"]=="RAI" and float(action["betsize"]) > 0 else "")
                   for action in actions_data]
        return actions

    def write_state(self):
        with open(self.PICKLE_PATH, 'wb') as f:
            pickle.dump(self.state, f)

    def load_state(self):
        try:
            with open(self.PICKLE_PATH, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []

    def get_line(self):
        line = []
        for actions, pos in self.state:
            line.append(actions[pos])
        return "-".join(line)

    def move_pointer(self):
        actions, pos = self.state[-1]
        self.state.pop()
        self.state.append((actions, pos + 1))
        if self.state[-1][1] >= len(actions):
            self.state.pop()
            self.move_pointer()

    def step(self, line: str):
        try:
            next_actions_data = self.get_next_actions(line)
            self.save_children_json(line, next_actions_data)
            actions_list = self.get_action_list(next_actions_data)
        except JSONDecodeError:
            logger.warning('JSONDecodeError')
            actions_list = []
        print("children:", actions_list)
        if not actions_list:
            self.move_pointer()
        else:
            self.state.append((actions_list, 0))

    def save_table(self, line: str):
        if line + ".json" in os.listdir(self.DATA_PATH):
            return
        try:
            solutions_data = self.get_solution(line)
            assert "solutions" in solutions_data
            self.save_solution_json(line, solutions_data)
        except json.JSONDecodeError:
            # self.move_pointer()
            logger.warning('JSONDecodeError solutions')

    def run(self):
        self.state = self.load_state()
        while True:
            line = self.get_line()
            logger.debug('Line: {}', line)
            self.save_table(line)
            self.step(line)
            self.write_state()
            print(self.state)

            time.sleep(5)


if __name__ == '__main__':
    parser = Parser()
    parser.run()

    # # parse_line([])
    # # get_next_actions([])
    #
    # next_actions_data = parser.get_next_actions(["F"])
    # next_actions_json = json.loads(next_actions_data)
    # actions_list = parser.get_action_list(next_actions_json)
    # print(actions_list)


# ([f, c, r6], 0)
# ([f, c, r6], 1)
# ([f, c, r6], 0)
# ([f, c, r6], 0)
# ([f, c, r6], 0)
# ([f, c, r6], 0)
# ([f, c, r6], 0)
# ([f, c, r6], 1)
# ([f, c, r6], 2)
# ([], 0)
#


