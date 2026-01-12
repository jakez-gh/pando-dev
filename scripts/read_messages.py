import os
p='pando_messages.jsonl'
if not os.path.exists(p):
    print('no file')
else:
    with open(p,'r',encoding='utf-8') as f:
        lines = f.read().splitlines()
    for l in lines[-20:]:
        print(l)
