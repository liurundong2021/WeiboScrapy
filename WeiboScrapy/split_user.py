import re
import os


size = 200
flag = False
file = './data/北京_04-01-00_04-17-00/users.jsonl'

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
