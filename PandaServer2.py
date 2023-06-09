import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from flask import Flask, request,jsonify
import numpy
import tensorflow
import random
import json
import nltk
from nltk.stem.lancaster import LancasterStemmer
from tensorflow import keras
nltk.download('punkt')
stemmer = LancasterStemmer()


app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/hello')
def fuckPy():
    return '파이썬 화나네'

@app.route('/api/sendAssociation',methods=['GET','POST'])
def receiveData():
    recData=request.get_json()
    # print(recData)
    # print(recData['myList'])
    # print(recData['otherList']['b1234567@email.com'])

    # 'otherList' 값 가져오기
    myList= recData['myList']
    otherList = recData['otherList']

    # 값들을 '/'로 분리하여 2차원 배열로 만들기(다른사람 것들)
    values_array = []
    for email, value in otherList.items():
        value_list = value.split('/')
        values_array.append(value_list)

    # 값들을 정수로 형변환
    for value_list in values_array:
        for i in range(len(value_list)):
            value_list[i] = int(value_list[i])


    print(values_array)
    print(set(myList))

    te=TransactionEncoder()
    te_ary=te.fit(values_array).transform(values_array)
    df=pd.DataFrame(te_ary,columns=te.columns_)
    #사용자 리스트
    userSet=set(myList)


    frequent_itemsets=apriori(df,min_support=0.1, use_colnames=True)

    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=0.1)
    result = rules[['lift', 'antecedents', 'consequents']].values

    df_result = pd.DataFrame(result, columns=['lift', 'antecedents', 'consequents'])  #향상도, 인과관계 변수2개(antecedents,consequents)만 뽑아냄
    sorted_result = df_result.sort_values(by='lift', ascending=False).values  #향상도 순으로 정렬

    recommendSet=[]

    for items in sorted_result:
        if set(items[1]).issubset(userSet) and items[0]>1:    #향상도가 1이상 이고, 사용자가 구매or조회한 제품 선택
            # print(items)
            recommendSet.append(items[2])


    normal_array = [list(item) for item in recommendSet]  #frozenset인거 일반 list타입으로 변경

    list2 = sum(normal_array, [])   #1차원 배열로 만듦

    list3=list(set(list2))  #중복 제거과정
    print(list3)


    data = {
        # 'name': 'John',
        # 'age': 30,
        # 'city': 'New York',
        'list': list3
    }
    return jsonify(data)

@app.route('/chatbot',methods=['GET','POST'])
def chatbotData():
    with open('intents.json', 'rb') as file:
        file_content = file.read().decode('utf-8')

    data = json.loads(file_content)

    words = []
    labels = []
    docs_x = []
    docs_y = []

    for intent in data['intents']:
        for pattern in intent['patterns']:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent['tag'] not in labels:
            labels.append(intent['tag'])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"]
    words = sorted(list(set(words)))

    labels = sorted(labels)

    training = []
    output = []

    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []

        wrds = [stemmer.stem(w.lower()) for w in doc]

        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)

    tensorflow.compat.v1.reset_default_graph()
    model = keras.models.load_model("model.h5")

    inp = request.get_data(as_text=True)
    print('전달된 문자열:', inp)

    results = model.predict([bag_of_words(inp, words)])

    max_prob = max(results[0])

    if max_prob < 0.5:
        return '이해가 가질 않습니다'
    else:
        results_index = numpy.argmax(results)
        tag = labels[results_index]

        for tg in data["intents"]:
            if tg['tag'] == tag:
                responses = tg['responses']

        message = random.choice(responses)
        print(message)

        return message

def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return numpy.array(bag).reshape(1, -1)

if __name__ == '__main__':
    app.run()