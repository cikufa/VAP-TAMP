"""API-boundary scripts only. No scene, hidden condition, physics or planner access."""
from .recording import MOCK_LABEL
class MockBackend:
    provider='mock';model='mock-script-v1'
    def __init__(self,script,log):
        if script not in ('straight','replan'):raise ValueError(script)
        self.script,self.log=script,log;self.direction_sent=False
    def request(self,payload,round_number):
        parts=payload['messages'][-1]['content'];text=' '.join(p['text'] for p in parts if p['type']=='text')
        is_left='left' in text and 'socket' in text
        if 'Choose the single best direction' in text:
            answer='right';self.direction_sent=True
        elif 'assessing whether' in text:
            answer='no' if self.script=='replan' and is_left and not self.direction_sent else 'yes'
        else:answer='no' if self.script=='replan' and is_left else 'yes'
        self.log('vlm_request',round=round_number,provider=self.provider,model=self.model,payload=payload,
                 label=MOCK_LABEL)
        self.log('vlm_response',round=round_number,provider=self.provider,model=self.model,answer=answer,
                 http_status=None,label=MOCK_LABEL)
        return answer
