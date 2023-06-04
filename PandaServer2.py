import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from flask import Flask, request,jsonify

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


if __name__ == '__main__':
    app.run()