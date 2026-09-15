"""Authenticated availability check for the exact released identifier; no fallback."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
MODEL='gpt-4-turbo'

def main():
    load_dotenv(ROOT/'.env', override=False)
    key=os.getenv('OPENAI_API_KEY')
    if not key:
        raise SystemExit('OPENAI_API_KEY is absent; no authenticated model check performed')
    response=requests.get('https://api.openai.com/v1/models/'+MODEL,
                          headers={'Authorization':'Bearer '+key},timeout=30)
    # Never log request headers or API error messages (which may echo credentials).
    data=response.json()
    result=dict(checked_utc=datetime.now(timezone.utc).isoformat(),requested_model=MODEL,
                http_status=response.status_code,model_id=data.get('id') if response.ok else None,
                error_code=data.get('error',{}).get('code') if not response.ok else None,
                scope='model access only; vision query accuracy not tested')
    out=ROOT/'results/original/model_access'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True,exist_ok=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    if not response.ok:
        raise SystemExit('Exact released model access check failed; no model substituted')

if __name__=='__main__':main()
