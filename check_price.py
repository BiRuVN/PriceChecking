# -*- coding: utf-8 -*-
import pandas as pd
import re
from underthesea import word_tokenize, ner
import time

def read_txt(f_path):
    f = open(f_path, encoding="utf8")
    if f.mode == 'r':
        content = f.read()
    return content.split('\n')

stopwords = read_txt('stopwords.txt')

# Remove stopwords
def remove_stopword(text):
    tokens = word_tokenize(text)
    return " ".join(word for word in tokens if word not in stopwords)

df = pd.read_csv('one_houses01.csv')
arr_description = []
set_abbreviate = { 'phòng ngủ': ['pn', 'phn'],
            'phòng khách': ['pk', 'phk'],
            'phòng vệ sinh': ['wc', 'tolet', 'toilet'],
            'hợp đồng': ['hđ', 'hd'],
            'đầy đủ': ['full'],
            'nhỏ': ['mini'],
            'tầm nhìn': ['view'],
            'địa chỉ': ['đc', 'đ/c'],
            'miễn phí': ['free'],
            'vân vân' : ['vv'],
            'liên hệ' : ['lh'],
            'trung tâm thành phố': ['tttp'],
            'yêu cầu': ['order'],
            'công viên': ['cv', 'cvien'],
            'triệu /' : [' tr/', ' tr /', ' tr ', 'tr/', 'tr /', 'tr '],
            ' triệu' : ['000000', 'trieu'],
            'phường' : [' p ', ' ph '],
            'quận' : [' q ', ' qu '],
            }

def replace_abbreviate(s):
    for key in set_abbreviate:
        s = re.sub('|'.join(set_abbreviate[key]),' {} '.format(key), s)
    return s

for index in range(len(df.index)):
    arr = [re.sub('[+|()]', ' ', line.lower()) for line in df.iloc[index]["description"].split('\n')]
    arr = [re.sub('[,]', '.', line) for line in arr if line != '']
    arr = [replace_abbreviate(line) for line in arr]
    arr = [re.sub('[^0-9A-Za-z ạảãàáâậầấẩẫăắằặẳẵóòọõỏôộổỗồốơờớợởỡéèẻẹẽêếềệểễúùụủũưựữửừứíìịỉĩýỳỷỵỹđ/%,.]', ' ', line) for line in arr]
    arr = [re.sub('m2', ' m2', line) for line in arr]
    arr = [" ".join(line.split()) for line in arr]
    arr_description.append((". ".join(arr)))
    
df = df.assign(description_2 = arr_description)

num = read_txt('numbers.txt')

def extract_info(tags):
    numbers_temp = []
    for i in range (len(tags)):
        if tags[i][1] == 'M':
            temp = ''
            for j in range (i, i+5):
                try:
                    temp = temp + ' ' + tags[j][0]
                    if tags[j][1] != 'Nu' and tags[j][1] != 'N':
                        continue
                    else:
                        break
                except IndexError:
                    pass
            if any(character.isdigit() for character in temp):
                numbers_temp.append(temp)
        elif any(character.isdigit() for character in tags[i][0]):
            numbers_temp.append(tags[i][0])
        
    return numbers_temp

start = time.time()
numbers_list = []
df['check_price'] = [0]*len(df)
df['price_bool'] = ['']*len(df)
for i in range (len(df)):
    text = df['description_2'][i]
    t = " ".join(remove_stopword(text).split())
    tags = ner(t)
    n = extract_info(tags)
    numbers_list.append(n)
    
    #   Check 2tr, 2tr5, 2 trieu, 2 triệu
    price_tr = [e for e in n if 'tr' in e]
    if len(price_tr) > 0:
        try:
            x = price_tr[0]
            x = x.replace(' triệu', 'triệu')
            x = x.replace('tr .', 'triệu')
            x = x.replace('/ tháng', '')
            x = x.replace('/ thang', '')
            x = x.replace(' tháng', '').strip()
            if 'triệu' in x:
                p = [e for e in x.split(' ') if 'triệu' in e]
                temp = p[0].replace('triệu', '000000')
                if '.' in temp:
                    df['check_price'][i] = float(temp)*1000000
                else:
                    df['check_price'][i] = float(temp)
                df['price_bool'][i] = abs(df['check_price'][i] - df['price'][i]) < 10000
            else:
                p = x.split('tr')
                if p[1].isdigit():
                    df['check_price'][i] = float(p[0])*1000000 + float(p[1])*100000
                else:
                    df['check_price'][i] = float(p[0])*1000000 
                df['price_bool'][i] = abs(df['check_price'][i] - df['price'][i]) < 10000    
        except ValueError:
            print(x)
    
    #   Check 2.000.000
    if df['check_price'][i] == 0:
        price_num = [e for e in n if '.000' in e and len(e) > 8]
        if len(price_num) > 0:
            try:
                x = price_num[0]
                x = x.replace('.', '').strip()
                x = x.split(' ')[0]
                df['check_price'][i] = float(x)
                df['price_bool'][i] = abs(df['check_price'][i] - df['price'][i]) < 10000
            except:
                print(x)
end = time.time()
print(end-start)
