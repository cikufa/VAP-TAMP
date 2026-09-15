from PIL import Image
import base64
import io
import numpy as np
from vlm_backends import build_backend


class GPT4VAgent:
    def __init__(self):
        self.prompt = "prompts.txt"
        self.planning_prompt = "planning_prompts.txt"
        self.backend = build_backend()
        self.max_tokens = 50
        # self.temperature = self.cfg["temperature"]
        self.errors = {}
        self.responses = {}
        self.current_round = 0
        self.gpt_version = self.backend.model
        # self.resize = transforms.Resize((self.cfg["img_size"], self.cfg["img_size"]))

    def reset(self):
        self.errors = {}
        self.responses = {}
        self.current_round = 0

    # def log_output(self, path):
    #     print("log gpt4v responses...")
    #     with open(os.path.join(path, "gpt4v_errs.json"), "w") as f:
    #         json.dump(self.errors, f, indent=4)
    #     with open(os.path.join(path, "responses.json"), "w") as f:
    #         json.dump(self.responses, f, indent=4)
    #     if self.goal:  # TODO: a few episodes' goals are None
    #         with open(os.path.join(path, "goal.txt"), "w") as f:
    #             f.write(self.goal)

    def _prepare_samples(self, obs, questions, debug_path=None):
        context_messages = []
        pil_image = Image.fromarray(obs)
        pil_image = pil_image.resize((256, 256))
        image_bytes = io.BytesIO()
        # if debug_path:
        #     round_path = os.path.join(debug_path, str(self.current_round))
        #     os.makedirs(round_path, exist_ok=True)
        #     pil_image.save(os.path.join(round_path, str(img_id) + ".png"))
        pil_image.save(image_bytes, format="png")
        base64_image = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
        text_img = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
        }
        context_messages.append({"type": "text", "text": questions})
        context_messages.append(text_img)

        chat_input = {
            "model": self.gpt_version,
            "messages": [
                {"role": "system", "content": open(self.prompt).read()},
                {"role": "user", "content": context_messages},
            ],
            "max_tokens": self.max_tokens,
            # "temperature": self.temperature,
        }
        return chat_input

    def _request_gpt4v(self, chat_input, num_questions=-1):
        res = self.backend.request(chat_input, self.current_round)
        print(f'{self.backend.provider} VLM response received')
        self.responses[self.current_round] = res
        return res, False

    def plan(self, problem, domain):
        problem_description = open(problem).read()
        domain_knowledge = open(domain).read()
        system_prompts = open(self.planning_prompt).read()
        context_messages = [
            {
                "type": "text",
                "text": f"Problem definition:\n{problem_description}\n"
                + f"Domain knowledge:\n{domain_knowledge}\n"
                + "Plan:\n",
            }
        ]
        chat_input = {
            "model": self.gpt_version,
            "messages": [
                {"role": "system", "content": system_prompts},
                {"role": "user", "content": context_messages},
            ],
            "max_tokens": 1000,
            # "temperature": self.temperature,
        }
        retry = True
        while retry:
            ans, retry = self._request_gpt4v(chat_input)
        ans = ans.lower().split(";")

        # form pddl_output.txt
        pddl_output = ""
        for action in ans:
            pddl_output += '(' + action.strip() + ')\n'
        pddl_output += f"; cost = {len(ans)} (unit cost)"
        with open('pddl_output.txt', 'w') as f:
            f.write(pddl_output)

        ret = []
        for action in ans:
            action_list = action.strip().split(" ")
            action_list.append("(1)") # add unit cost
            ret.append(action_list[:])
        return ret

    def ask(
        self,
        questions,
        obs,
        debug_path=None,
    ):
        if obs is None:
            return None
        self.current_round += 1
        chat_input = self._prepare_samples(obs, questions, debug_path=debug_path)
        retry = True
        while retry:
            ans, retry = self._request_gpt4v(chat_input, len(questions.split(";")))
        ans = ans.lower().split(";")
        return ans
