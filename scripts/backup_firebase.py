"""Firebase Realtime DB(greenfee/db, greenfee/holidays, greenfee/engine, greenfee/engine_log) -> data/*.json
공개 설정값(apiKey, databaseURL)은 index.html에서 읽는다. 비밀키 불필요.
"""
import json, re, os, sys, urllib.request, urllib.error

html = open('index.html', encoding='utf-8').read()
API_KEY = re.search(r'apiKey:\s*"([^"]+)"', html).group(1)
DB_URL  = re.search(r'databaseURL:\s*"([^"]+)"', html).group(1).rstrip('/')

def http(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode())

def read(path, token=None):
    return http(f'{DB_URL}/{path}.json' + (f'?auth={token}' if token else ''))

token = None
try:
    raw = read('greenfee/db')                       # 규칙이 공개 읽기면 로그인 없이
except urllib.error.HTTPError:
    token = http(f'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}',
                 {'returnSecureToken': True})['idToken']   # 사이트와 같은 익명 로그인
    raw = read('greenfee/db', token)

def unpack(node):
    if not node: return {}
    return json.loads(node['data']) if isinstance(node, dict) and 'data' in node else node

db = unpack(raw)
if not db:
    print('데이터가 비어 있음 - 기존 백업을 덮어쓰지 않음'); sys.exit(0)
hol = unpack(read('greenfee/holidays', token))
def safe(path):                                          # 새 경로를 못 읽어도 그린피 백업은 계속
    try: return read(path, token)
    except Exception as e: print(f'{path} 읽기 건너뜀: {e}'); return None
eng = unpack(safe('greenfee/engine'))                    # 적정 그린피 설정 (knh 프로그램에서 저장)
elog = safe('greenfee/engine_log') or {}                 # 설정 변경 이력

os.makedirs('data', exist_ok=True)
json.dump(db,  open('data/greenfee_db.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
json.dump(hol, open('data/greenfee_holidays.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
if eng: json.dump(eng, open('data/greenfee_engine.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
if elog: json.dump(elog, open('data/greenfee_engine_log.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
n = sum(len(v) for d in db.values() for v in d.values())
print(f'백업 완료: 날짜 {len(db)}개, 골프장 기록 {n}건, 적정가 설정 {"있음" if eng else "없음"}, 설정 이력 {len(elog)}건')
