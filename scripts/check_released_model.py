"""Authenticated text-and-image check for the configured reproduction model."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
# A valid 1x1 PNG. This verifies the same image-input route used by VAP-TAMP
# without launching the simulator or storing image payloads in the result.
IMAGE_DATA_URL=('data:image/png;base64,'
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC'
                'AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')

def main():
    load_dotenv(ROOT/'.env', override=False)
    model=os.getenv('VAPTAMP_OPENAI_MODEL', 'gpt-4o-2024-05-13')
    key=os.getenv('OPENAI_API_KEY')
    if not key:
        raise SystemExit('OPENAI_API_KEY is absent; no authenticated model check performed')
    headers={'Authorization':'Bearer '+key, 'Content-Type':'application/json'}
    response=requests.get('https://api.openai.com/v1/models/'+model,
                          headers=headers,timeout=30)
    # Never log request headers or API error messages (which may echo credentials).
    data=response.json()
    result=dict(checked_utc=datetime.now(timezone.utc).isoformat(),requested_model=model,
                http_status=response.status_code,model_id=data.get('id') if response.ok else None,
                error_code=data.get('error',{}).get('code') if not response.ok else None,
                scope='model lookup')
    if response.ok:
        vision=requests.post('https://api.openai.com/v1/chat/completions', headers=headers,
            json={'model':model,'messages':[{'role':'user','content':[
                {'type':'text','text':'Reply with exactly: image-ok'},
                {'type':'image_url','image_url':{'url':IMAGE_DATA_URL}}]}],
                'max_tokens':8}, timeout=30)
        vision_data=vision.json()
        result.update(vision_http_status=vision.status_code,
                      vision_error_code=(vision_data.get('error',{}).get('code')
                                         if not vision.ok else None),
                      returned_model=vision_data.get('model') if vision.ok else None,
                      vision_response_present=bool(vision_data.get('choices')))
    out=ROOT/'results/original/model_access'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True,exist_ok=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    if not response.ok:
        raise SystemExit('Configured reproduction model lookup failed')
    if result['vision_http_status'] != 200 or not result['vision_response_present']:
        raise SystemExit('Configured reproduction model image request failed')

if __name__=='__main__':main()
