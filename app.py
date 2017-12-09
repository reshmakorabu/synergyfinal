from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo

import RAKE.RAKE as rake
import operator
from operator import itemgetter
import csv
import sys
import datetime


app = Flask(__name__)

app.config['MONGO_DBNAME'] = "todo"
app.config['MONGO_URI'] = "mongodb://sh221:sh221@ds129344.mlab.com:29344/todo"
app.config['SECRET_KEY']='synergy1234'
#app.config['MONGO_URI'] = "mongodb://localhost:33333/todo"

mongo = PyMongo(app)

@app.route('/')
@app.route('/index', methods=['POST','GET'])
def index():
    blogs= mongo.db.blogs
    if request.method=='POST':
        if 'logout' in request.form:
            print("logout")
            session.clear()
            return redirect(url_for('index'))
        elif 'submit' in request.form:
            print("blog")
            blog= request.form['blog']
            #users=mongo.db.users
            #users.update({'username': session['username']}, {'$push': {'blogs':{'text':blog, 'timestamp':datetime.datetime.utcnow()}}})

            blogs.insert_one({'username':session['username'], 'blog': blog, 'timestamp':datetime.datetime.utcnow(), 'comments':[]})
            return redirect(url_for('index'))
        else:
            comment = request.form['comments']
            print(comment)
            blog = request.args.get('values')
            print(blog)
            blogs.update({'blog': blog}, {'$push': {'comments':comment}})
            return redirect(url_for('index'))
            
    else:  
        if 'username' in session:
            #return 'You are logged in as ' + session['username']
            people =[session['username']]
            users = mongo.db.users
            i = users.find_one({'username':session['username']})
            people.extend(i['following'])
            blogdata=[]
            for name in people:
                data = blogs.find({'username': name})
                for x in data:
                    blogdata.append(x)
            #blogdata = blogs.find({"$and": [{'username': { "$ne" : username}},{'domain': element},{'status':status}]})
            #blogs.extend(record['blogs'])
            #for rec in record['following']:
                #user= users.find_one({'username': rec})
               # blogs.extend()
            new_list = sorted(blogdata, key=itemgetter('timestamp'), reverse=True)
            #print(new_list)
            details=[]
            for x in new_list:
                rec= users.find_one({'username': x['username']})
                details.append({'status': rec['status'], 'gender': rec['gender']})
            
            list_res= find_friends(session['username'])
            result=[]
            seen =set()
            rec= users.find_one({'username':session['username']})
            following = rec['following']
            #print(following)
            for d in list_res:
                if d['username'] in following:
                    print(d['username'])
                elif d['username'] not in seen:
                    seen.add(d['username'])
                    result.append(d)
                else:
                    new_value= d['value']*2
                    #index=map(itemgetter('username'), new_list).index(d['username'])
                    x = next(item for item in result if item['username'] == d['username'])
                    index=result.index(x)
                    result[index]['value']=result[index]['value']*2+new_value

            newlist = sorted(result, key=itemgetter('value'), reverse=True)
            count=len(newlist)
            
            users=mongo.db.users
            list_res1 = find_recom(session['username'])
            new_list1=[]
            seen =set()
            rec1= users.find_one({'username':session['username']})
            following = rec1['following']
            #print(following)
            for d in list_res1:
                if d['username'] in following:
                    print(d['username'])
                elif d['username'] not in seen:
                    seen.add(d['username'])
                    new_list1.append(d)
                else:
                    new_value= d['value']*2
                    #index=map(itemgetter('username'), new_list).index(d['username'])
                    x = next(item for item in new_list1 if item['username'] == d['username'])
                    index=new_list1.index(x)
                    new_list1[index]['value']=new_value

            newlist1 = sorted(new_list1, key=itemgetter('value'), reverse=True)
            count1=len(newlist1)
            return render_template("Trial/index.html",list=zip(new_list,details),newlist=newlist,count=count,recomlist=newlist1,count1=count1)

        return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'username' : request.form['username']})

    if login_user:
        #if bcrypt.checkpw(request.form['pass'].encode('utf-8'),login_user['password'].encode('utf-8')):
        #if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
        if request.form['pass']==login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))

    return 'Invalid username/password combination'

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        
        existing_user= users.find_one({'username': request.form['username']})

        if existing_user is None:
            #hashpass = bcrypt.hashpw(request.form['userpassword'].encode('utf-8'), bcrypt.gensalt())
            hashpass= request.form['userpassword']
            aboutMe= request.form['user_bio']
            domain, score = classify_text(aboutMe)
            print(domain)
            #print(score)
            users.insert({'username': request.form['username'], 'password': hashpass, 'name': request.form['fullname'], 'email': request.form['mail'], 'gender': request.form['gender'], 'college': request.form['cname'], 'status': request.form['gyear'], 'aboutMe': aboutMe, 'domain': domain, 'score' : score, 'value': 0.0, 'following':[],'followers':[]})

            session['username'] = request.form['username']
            return redirect(url_for('index'))
        
        return 'That username already exists!'

    return render_template('register1.html')
    
def word2vec(word):
    from collections import Counter
    from math import sqrt

    # count the characters in word
    cw = Counter(word)
    # precomputes a set of the different characters
    sw = set(cw)
    # precomputes the "length" of the word vector
    lw = sqrt(sum(c*c for c in cw.values()))

    # return a tuple
    return cw, sw, lw

def cosdis(v1, v2):
    # which characters are common to the two words?
    common = v1[1].intersection(v2[1])
    # by definition of cosine distance we have
    return sum(v1[0][ch]*v2[0][ch] for ch in common)/v1[2]/v2[2]


def classify_text(text):
    rake_object = rake.Rake("SmartStoplist.txt")

    keywords = rake_object.run(text)
    #print("Keywords:", keywords)

    #above code successfully executed... Below code is extension. Could contain errors.


    words=[]
    scr=[]

    for phrase in keywords:
        if phrase[1]>0 :
            words.append(phrase[0])
            scr.append(phrase[1])


    #print(words)

    simpletext = []
    sometext = []
    with open('train.csv','r') as simple:
        sometext = csv.reader(simple)
        for row in sometext:
            tblb = ()
            tblb = (row[0],row[1])
            simpletext.append(tblb)



    domainlist=[]
    score=[]

    for word in words:
        max=0
        v1=word2vec(word)
        for d in simpletext:
            word2=d[0]
            v2=word2vec(word2)
            res= cosdis(v1,v2)
            if res>max:
                max=res
                index= simpletext.index(d)
        domain=simpletext[index][1]
        print(word+"----"+domain)
        if domain in domainlist:
            index1 = domainlist.index(domain)
            i=words.index(word)     
            score[index1]=score[index1]+scr[i] 
            #print(domain+'---'+str(score[index1]))
        else:
            domainlist.append(domain)
            i=words.index(word)
            score.append(scr[i])
            #print(domain+"---"+str(score[i]))
    print(domainlist)
    return domainlist, score
    


@app.route('/members',methods=['POST','GET'])
def members():
    return render_template('Trial/members.html')


@app.route('/getprofile',methods=['POST','GET'])
def getprofile():
    users=mongo.db.users
    username = request.args.get('values')
    record= users.find_one({'username': username})
    list_res= find_friends(session['username'])
    result=[]
    seen =set()
    rec= users.find_one({'username':session['username']})
    following = rec['following']
            #print(following)
    for d in list_res:
        if d['username'] in following:
             print(d['username'])
        elif d['username'] not in seen:
            seen.add(d['username'])
            result.append(d)
        else:
            new_value= d['value']*2
                    #index=map(itemgetter('username'), new_list).index(d['username'])
            x = next(item for item in result if item['username'] == d['username'])
            index=result.index(x)
            result[index]['value']=result[index]['value']*2+new_value

    newlist = sorted(result, key=itemgetter('value'), reverse=True)
    count=len(newlist)
            
    users=mongo.db.users
    list_res1 = find_recom(session['username'])
    new_list1=[]
    seen =set()
    rec1= users.find_one({'username':session['username']})
    following = rec1['following']
            #print(following)
    for d in list_res1:
        if d['username'] in following:
            print(d['username'])
        elif d['username'] not in seen:
            seen.add(d['username'])
            new_list1.append(d)
        else:
            new_value= d['value']*2
                    #index=map(itemgetter('username'), new_list).index(d['username'])
            x = next(item for item in new_list1 if item['username'] == d['username'])
            index=new_list1.index(x)
            new_list1[index]['value']=new_value

    newlist1 = sorted(new_list1, key=itemgetter('value'), reverse=True)
    count1=len(newlist1)
    return render_template('Trial/profile.html',record=record,newlist=newlist,count=count,recomlist=newlist1,count1=count1)

@app.route('/profile')
def profile():
    users= mongo.db.users
    record = users.find_one({'username':session['username']})
    list_res= find_friends(session['username'])
    result=[]
    seen =set()
    rec= users.find_one({'username':session['username']})
    following = rec['following']
            #print(following)
    for d in list_res:
        if d['username'] in following:
             print(d['username'])
        elif d['username'] not in seen:
            seen.add(d['username'])
            result.append(d)
        else:
            new_value= d['value']*2
                    #index=map(itemgetter('username'), new_list).index(d['username'])
            x = next(item for item in result if item['username'] == d['username'])
            index=result.index(x)
            result[index]['value']=result[index]['value']*2+new_value

    newlist = sorted(result, key=itemgetter('value'), reverse=True)
    count=len(newlist)
            
    users=mongo.db.users
    list_res1 = find_recom(session['username'])
    new_list1=[]
    seen =set()
    rec1= users.find_one({'username':session['username']})
    following = rec1['following']
            #print(following)
    for d in list_res1:
        if d['username'] in following:
            print(d['username'])
        elif d['username'] not in seen:
            seen.add(d['username'])
            new_list1.append(d)
        else:
            new_value= d['value']*2
                    #index=map(itemgetter('username'), new_list).index(d['username'])
            x = next(item for item in new_list1 if item['username'] == d['username'])
            index=new_list1.index(x)
            new_list1[index]['value']=new_value

    newlist1 = sorted(new_list1, key=itemgetter('value'), reverse=True)
    count1=len(newlist1)
    return render_template('Trial/profile.html',record=record,newlist=newlist,count=count,recomlist=newlist1,count1=count1)

@app.route('/friends', methods=['GET','POST'])
def friends():
    if request.method=='POST':
        record=request.form['record']
        #print("record--"+record)
        users=mongo.db.users
        users.update({'username': session['username']}, {'$push': {'following':record}})  
        users.update({'username': record}, {'$push': {'followers':session['username']}})  
        return redirect(url_for('friends'))
        
    else:
        users=mongo.db.users
        list_res = find_friends(session['username'])
        new_list=[]
        seen =set()
        rec= users.find_one({'username':session['username']})
        following = rec['following']
        #print(following)
        for d in list_res:
            if d['username'] in following:
                print(d['username'])
            elif d['username'] not in seen:
                seen.add(d['username'])
                new_list.append(d)
            else:
                new_value= d['value']*2
                #index=map(itemgetter('username'), new_list).index(d['username'])
                x = next(item for item in new_list if item['username'] == d['username'])
                index=new_list.index(x)
                new_list[index]['value']=new_list[index]['value']*2+new_value

        newlist = sorted(new_list, key=itemgetter('value'), reverse=True)
        #print(newlist)
        return render_template('Trial/friends.html',new_list=newlist)

def find_friends(username):
    users= mongo.db.users
    curr_user = users.find({'username':username})
    # profiles is a collection with all the user details 
    first=curr_user[0]
    result=[]
    if first['status']=='student':
        status='student'
    else:
        status='alumni'
    for doc in curr_user:
        lst = doc['domain']
        for element in lst:
            #print(element)
            index = lst.index(element)
            #print(doc['score'][index])
            #{doc['following']:{"$nin":[doc['username']]}},
            list = users.find({"$and": [{'username': { "$ne" : username}},{'domain': element},{'status':status}]})
            for d in list:
                #print(d['username'])
                i = d['domain'].index(element)
                new_value = d['score'][i]
                #print("new val:"+ str(new_value))
                users.update_one({
                        "_id" : d['_id']
                    },{
                          '$set': 
                          {
                              'value': new_value
                              #value field is to maintain score of one particular domain
                          }
                        }, upsert=False)
                
                #print(d['value'])
               # doc.sort('value':-1)
        
            cur = users.find({"$and": [{'username': { "$ne" : username}},{'domain': element},{'status':status}]})      
            cursor = cur.sort([('value', -1)]).limit(5) 
            
            for rec in cursor:
                #print("rec--"+str(rec))
                result.append(rec)
    #print(result)
    return result
       
@app.route('/following',methods=['GET'])
def following():
    users=mongo.db.users
    record=users.find_one({'username': session['username']})
    lst= record['following']
    new_list=[]
    for name in lst:
        rec= users.find_one({'username':name})
        new_list.append(rec)
    return render_template('Trial/following.html',new_list=new_list)

@app.route('/followers',methods=['GET'])
def followers():
    users=mongo.db.users
    record=users.find_one({'username': session['username']})
    lst= record['followers']
    new_list=[]
    for name in lst:
        rec= users.find_one({'username':name})
        new_list.append(rec)
    return render_template('Trial/followers.html',new_list=new_list)

@app.route('/recommendations',methods=['GET','POST'])
def recommendatins():
    if request.method=='POST':
        record=request.form['record']
        print("record--"+record)
        users=mongo.db.users
        users.update({'username': session['username']}, {'$push': {'following':record}})    
        users.update({'username': record}, {'$push': {'followers':session['username']}})   
        return redirect(url_for('recommendations'))
        
    else:
        users=mongo.db.users
        list_res = find_recom(session['username'])
        new_list=[]
        seen =set()
        rec= users.find_one({'username':session['username']})
        following = rec['following']
        print(following)
        for d in list_res:
            if d['username'] in following:
                print(d['username'])
            elif d['username'] not in seen:
                seen.add(d['username'])
                new_list.append(d)
            else:
                new_value= d['value']*2
                #index=map(itemgetter('username'), new_list).index(d['username'])
                x = next(item for item in new_list if item['username'] == d['username'])
                index=new_list.index(x)
                new_list[index]['value']=new_value

        newlist = sorted(new_list, key=itemgetter('value'), reverse=True)
        #print(newlist)
        return render_template('Trial/friends.html',new_list=newlist)
    
def find_recom(username):
    users= mongo.db.users
    curr_user = users.find({'username':username})
    # profiles is a collection with all the user details 
    first=curr_user[0]
    result=[]
    if first['status']=='student':
        status='alumni'
    else:
        status='student'
    for doc in curr_user:
        lst = doc['domain']
        for element in lst:
            #print(element)
            index = lst.index(element)
            #print(doc['score'][index])
            #{doc['following']:{"$nin":[doc['username']]}},
            list = users.find({"$and": [{'username': { "$ne" : username}},{'domain': element},{'status':status}]})
            for d in list:
                #print(d['username'])
                i = d['domain'].index(element)
                new_value = d['score'][i]
                #print("new val:"+ str(new_value))
                users.update_one({
                        "_id" : d['_id']
                    },{
                          '$set': 
                          {
                              'value': new_value
                              #value field is to maintain score of one particular domain
                          }
                        }, upsert=False)
                
                #print(d['value'])
               # doc.sort('value':-1)
        
            cur = users.find({"$and": [{'username': { "$ne" : username}},{'domain': element},{'status':status}]})      
            cursor = cur.sort([('value', -1)]).limit(3) 
            
            for rec in cursor:
                #print("rec--"+str(rec))
                result.append(rec)
    #print(result)
    return result

@app.route('/messenger',methods=['GET','POST'])
def messenger():
    if request.method=='GET':
        name= session['username']
        chat =mongo.db.chat
        rec=chat.find({"$or":[{'to':name},{'from':name}]})
        arr=[]
        for d in rec:
            to_user= d['to']
            from_user=d['from']
            if to_user==name:
                if from_user not in arr:
                    arr.append(from_user)
            else:
                if to_user not in arr:
                    arr.append(to_user)
        
        users= mongo.db.users
        gen=[]
        for rec in arr:
            record=users.find_one({'username':rec})
            gen.append(record['gender'])
        return render_template('Trial/messenger.html',list=zip(arr,gen))
    else:
        name1=request.args.get('values')
        return redirect(url_for('messages',values=name1))
        

@app.route('/messages',methods=['GET','POST'])
def messages():
    if request.method=='POST':
        username = request.args.get('values')
        #print("args:"+str(username))
        chat= mongo.db.chat
        from_user = session['username']
        to_user=username
        msg=request.form['message']
        rec= chat.find_one({'to':to_user, 'from':from_user})
        if rec:
            chat.update_one({'to':to_user, 'from':from_user}, {'$push': {'chat':{'timestamp':datetime.datetime.utcnow(), 'message':msg,'flg':0}}})
        else:
            chat.insert_one({'to':to_user, 'from':from_user, 'chat':[{'timestamp':datetime.datetime.utcnow(), 'message':msg, 'flg':0}]})
            
        return redirect(url_for('messages',values=username))
    else:
        username = request.args.get('values')
        if username is None:
            username=request.args['values']
        #print(username)
        name1=username
        name2=session['username']
        chat=mongo.db.chat
        result=[]
                    
        res1=chat.find({'to':name2, 'from':name1})
        res2=chat.find({'to':name1, 'from':name2})
        for d in res1:
            for obj in d['chat']:
                obj['flg']=0
                result.append(obj)
        for d in res2:
            for obj in d['chat']:
                obj['flg']=1
                result.append(obj)
        new_list = sorted(result, key=itemgetter('timestamp'), reverse=False)
    return render_template('Trial/chat.html',new_list=new_list,user_name=session['username'],user2=username)
    
    
if __name__ == '__main__':
    app.secret_key = 'mysecretkey'
    app.run(debug=True)