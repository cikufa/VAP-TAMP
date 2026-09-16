"""Read-only checks that image payloads are exactly tied to native observations."""
import base64,hashlib,io,json
import numpy as np
from PIL import Image
from .media import events

def image_requests(path,live=False):
    trace=events(path);observations={x['index']:x for x in trace if x['event']=='paper_sensor_observation'}
    bindings={x['round']:x for x in trace if x['event']=='paper_query_observation'}
    requests=[x for x in trace if x['event']=='vlm_request']
    for request in requests:
        if live and request['provider']=='mock':raise AssertionError('Mock backend in LIVE episode')
        payload=request.get('source_contract',request['payload'])
        part=next(p for p in payload['messages'][-1]['content'] if p['type']=='image_url')
        rgb=np.asarray(Image.open(io.BytesIO(base64.b64decode(part['image_url']['url'].split(',',1)[1]))))
        bound=bindings[request['round']];obs=observations[bound['observation']]
        assert hashlib.sha256(rgb.tobytes()).hexdigest()==obs['pixel_sha256']==bound['pixel_sha256']
        original=np.asarray(Image.open(obs['image']))
        assert np.array_equal(rgb,original)
    result=dict(requests=len(requests),all_payloads_match_native_observation=True,live=live,
        provider=sorted({x['provider'] for x in requests}),models=sorted({x['model'] for x in requests}))
    return result
