'''This function is for crawl user history.

If the time set for crawl history is long, crawl a user need many times,
especially YingXiaoHao, post many blogs a day. So you may best split the
user file first, then crawl them one by one, finally merge them.
'''

import re
import os


size = 200
flag = False
file = './data/淄博_04-01-00_04-17-00/users.jsonl'

output_path = re.search('(.*/)', file).group(1) + f'user_split_{size}/'
os.mkdir(output_path)

with open(file) as f:
    count = 1
    while 1:
        with open(output_path + f'{count}.jsonl', 'w') as f2:
            for i in range(size):
                line = f.readline()
                if not line:
                    flag = True
                    break

                f2.write(line)
        if flag:
            break

        count += 1
