#coding:utf-8
import pandas as pd
from pandas import DataFrame
import re
import cPickle as pickle
import math

class SpamFilter:
    def __init__(self,initial=0):
        if initial==0:
            #不是初次使用时，加载模型
            f = open('wordict','rb')
            self.wordict = pickle.load(f)
            f.close()
        else:
            #初次使用时新建模型
            self.wordict = {}
        #加载停用词列表
        f = open('stop','r')
        self.stop = f.readlines()
        f.close()
        self.stop = [i.strip().decode('gbk','ignore') for i in self.stop]
        #初始化dataframe
        self.df = pd.read_csv('full/index',sep=' ',names=['spam','path'])
        self.df.spam = self.df.spam.apply(lambda x:1 if x=='spam' else 0)
        self.df.path = self.df.path.apply(lambda x:x[1:])
        #预测用
        self.ham_count = self.getEmailList().spam.value_counts()[0]
        self.spam_count = self.getEmailList().spam.value_counts()[1]
        self.all_count = self.ham_count + self.spam_count

    def getContent(self,path):
        f = open(path,'r')
        content = f.readlines()
        f.close()
        for i in range(len(content)):
            if content[i] == '\n':
                content = content[i:]
                break
        content = ','.join(''.join([i.strip() for i in content]).split())
        return content.lower()

    def getEmailList(self,initial=0):
        if initial == 1:
            self.df['content'] = self.df.path.apply(lambda x:self.getContent(x))
            self.df['wordlist'] = self.df.content.apply(lambda x:pickle.dumps(self.getWordlist(x)))
        return self.df

    def stop_words(self,dic):
        for i in self.stop:
            if i in dic:
                del dic[i]
        return dic

    def getWordlist(self,string):
        wordlist = re.findall(r'[a-z]+',string)
        dic = dict([(w,1) for w in wordlist])
        #for i in wordlist:
        #    dic[i] += 1
        dic = self.stop_words(dic)
        return dic

    #训练模型
    def trainDict(self,dataframe):
        wordlists = dataframe.wordlist
        spams = dataframe.spam
        for wl,spam in zip(wordlists,spams):
            wordlist = pickle.loads(wl)
            for i in wordlist:
                self.wordict.setdefault(i,{0:0,1:0})
                self.wordict[i][spam] += 1
        #存模型
        f = open('wordict','wb')
        pickle.dump(self.wordict,f,1)
        f.close()
        print "Success"

    #threshold：阈值，预测的时候当然是ham的概率大些好，防止把正常邮件归为垃圾邮件
    def predictEmail(self,wordlist,threshold=0):
        hp = math.log(float(self.ham_count)/self.all_count)
        sp = math.log(float(self.spam_count)/self.all_count)
        wordlist = pickle.loads(wordlist)
        for i in wordlist:
            self.wordict.setdefault(i,{0:0,1:0})
            pih = self.wordict[i][0]
            if pih == 0:hp += math.log((1./(len(wordlist)+1))/(self.ham_count+1))
            else:hp += math.log(float(pih)/self.ham_count)
            pis = self.wordict[i][1]
            if pis == 0:sp += math.log((1./(len(wordlist)+1))/(self.spam_count+1))
            else:sp += math.log(float(pis)/self.spam_count)
        #print hp,sp
        if hp+threshold>sp:return 0
        else:return 1

def run(T=0):
    #训练模型
    #'''
    sf = SpamFilter(initial=1)
    all_mail = sf.getEmailList(initial=1)
    train_mail = all_mail.loc[:len(all_mail)*0.8]
    check_mail = all_mail.loc[len(all_mail)*0.8:]
    check_mail.to_csv('test_set')
    sf.trainDict(train_mail)
    #'''
    sf = SpamFilter()

    #评测
    threshold = T
    check_mail = pd.read_csv('test_set',index_col=0)
    check_mail['predict'] = check_mail.wordlist.apply(lambda x:sf.predictEmail(x,threshold))
    foo = check_mail.predict + check_mail.spam
    all_right = 1-float(foo.value_counts()[1])/foo.value_counts().sum()
    ham_right = float(foo.value_counts()[0])/check_mail.spam.value_counts()[0]
    print "Threshold:",threshold
    print "总体准确率：",all_right*100,'%'
    print "正常邮件获取度：",ham_right*100,'%'
    return (all_right,ham_right)


def draw():
    #画图用代码
    x_list = [i for i in range(-20,41,3)]
    y_list_1 = []
    y_list_2 = []
    for i in x_list:
        t = run(i)
        y_list_1.append(t[0])
        y_list_2.append(t[1])
    #存数据
    f = open('y_list_1','wb')
    pickle.dump(y_list_1,f,1)
    f.close()
    f = open('y_list_2','wb')
    pickle.dump(y_list_2,f,1)
    f.close()
    print y_list_1
    print y_list_2


if __name__ =='__main__':
    #run(0)
    draw()