from flask import Flask,render_template,request,url_for,session,jsonify,flash,redirect
from dbconnection.datamanipulation import *
import datetime


mail=Flask(__name__,template_folder='template')

mail.secret_key='supersecretkey'
@mail.route('/')
def index():
    return render_template('index.html')

@mail.route('/register')
def register():
    return render_template('register.html')

@mail.route('/registeraction',methods=['POST'])
def registeraction():
    name=request.form['name']
    address=request.form['address']
    gender=request.form['gender']
    country=request.form['country']
    phone=request.form['phone']
    username=request.form['username']
    password=request.form['password']

    reg=sql_edit_insert("insert into register_tb values(NULL,?,?,?,?,?,?,?)",(name,address,gender,country,phone,username+'@mymail.com',password))
    flash('registered successfully')
    return redirect(url_for('register'))
@mail.route('/checkusername')
def checkusername():
    us=request.args.get('nm')
    row=sql_query2("select * from register_tb where username=?",[us+'@mymail.com'])

    if(len(row)>0):
        msg="exist"
    else:
        msg="not exist"
    return jsonify({'valid':msg})

@mail.route('/login')
def login():
    return render_template('login.html')

@mail.route('/loginaction',methods=['POST'])
def loginaction():
    username=request.form['username']
    password=request.form['password']
    log=sql_query2("select * from register_tb where username=? and password=?",(username,password))

    if(len(log)>0):
        session['id']=log[0][0]
        msg="login successfull"
        session['username']=log[0][1]
        print(session['username'])
        return render_template('home.html',msg=msg)

    else:
        msg="login failed"
        return render_template('login.html',msg=msg)

@mail.route('/compose')
def compose():
    return render_template('sendmsg.html',uid=session['id'])

@mail.route('/checkreceivername')
def checkreceivername():
    rev=request.args.get('nam')
    row=sql_query2(" select * from register_tb where username=?",[rev])

    if(len(row)>0):
        msg="exist"
    else:
        msg="not exist"
    return jsonify({'valid':msg})
    
@mail.route('/sendmailaction',methods=['POST'])
def sendmailaction():
    sender=request.form['id']
    receiver=request.form['receivername']
    row=sql_query2("select * from register_tb where username=?",[receiver])
    receiverid=row[0][0]
    subject=request.form['subject']
    message=request.form['message']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime("%H: %M")
    send=sql_edit_insert("insert into message_tb values(NULL,?,?,?,?,?,?,?)",(sender,receiverid,message,subject,date,time,'pending'))

    if send>0:
        msg="msg send"
    else:
        msg="not send"
    return render_template('sendmsg.html',uid=session['id'],msg=msg)

@mail.route('/viewmessage')
def viewmessage():
    vmsg=sql_query2("select register_tb.username,message_tb.* from register_tb inner join message_tb on register_tb.id=message_tb.receiverid where senderid=? and status!=?",(session['id'],'deleted by sender'))
    return render_template('viewmessage.html',view=vmsg)

@mail.route('/deletemsg')
def deletemsg():
    id=request.args.get('uid')
    row=sql_query2("select * from message_tb where id=?",[id])
    status=row[0][7]

    if status=="deleted by receiver":
        query=sql_query2("delete from message_tb where id=?",[id])
        return redirect('viewmessage')

    else:
        query=sql_edit_insert("update message_tb set status=? where id=?",('deleted by sender',id))
        return redirect('viewmessage')

@mail.route('/inbox')
def inbox():
    query=sql_query2("select register_tb.username,message_tb.* from register_tb inner join message_tb on register_tb.id=message_tb.senderid where receiverid=? and message_tb.id not in(select messageid from trash_tb where userid=?) and status!=?",(session['id'],session['id'],'deleted by receiver'))
    return render_template('inbox.html',view=query)

@mail.route('/movetotrash',methods=['POST'])
def movetotrash():
    date=datetime.date.today()
    time=datetime.datetime.now().strftime("%H:%M")
    box=request.form.getlist('checkbox')
    for mid in box:
        query=sql_edit_insert("insert into trash_tb values(NULL,?,?,?,?)",(mid,session['id'],date,time))
    return redirect('inbox')

@mail.route('/viewtrash')
def viewtrash():
    query=sql_query2("select register_tb.username,message_tb.*,trash_tb.date,trash_tb.time from(register_tb inner join message_tb on register_tb.id=message_tb.senderid)inner join trash_tb on message_tb.id=trash_tb.messageid where userid=?",[session['id']])
    return render_template('viewtrash.html',view=query)

@mail.route('/delete')
def delete():
    sid=request.args.get('uid')
    sql_edit_insert("delete from trash_tb where messageid=?",[sid])
    msg=sql_query2("select * from message_tb where id=?",[sid])
    status=msg[0][7]
    if status=="deleted by sender":
        #query=sql_edit_insert("delete from message_tb where id=?",[sid])
        query=sql_edit_insert("update message_tb set status=? where id=?",("deleted",sid))
    else:
        query=sql_edit_insert("update message_tb set status=? where id=?",("deleted by receiver",sid))
    return redirect(url_for('viewtrash'))

@mail.route('/forwardmsg')
def forwardmsg():
    fid=request.args.get('uid')
    query=sql_query2("select * from message_tb where id=?",[fid])
    return render_template('forwardmsg.html',view=query,uid=fid)

@mail.route('/checkrec')
def checkrec():
    rec=request.args.get('re')
    row=sql_query2("select * from register_tb where username=?",[rec])

    if(len(row)>0):
        msg="exist"

    else:
        msg="not exist"
    return jsonify({'valid':msg})

@mail.route('/forwardmsgaction',methods=['POST'])
def forwardmsgaction():
    sender=request.form['id']
    query=sql_query2("select * from message_tb where id=?",[sender])
    receiver=request.form['receivername']
    row=sql_query2("select * from register_tb where username=?",[receiver])
    receiverid=row[0][0]
    mes=request.form['message']
    subject=request.form['subject']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime("%H:%M")
    
    q=sql_edit_insert("insert into message_tb values(NULL,?,?,?,?,?,?,?)",(session['id'],receiverid,mes,subject,date,time,'forwarded message'))
    if q>0:
        msg="msg send"
    else:
        msg="failed"
    return render_template('forwardmsg.html',view=query,msg=msg)

@mail.route('/reply')
def reply():
    rid=request.args.get('uid')
    query=sql_query2("select register_tb.username,message_tb.senderid from register_tb inner join message_tb on register_tb.id=message_tb.senderid where message_tb.id=?",[rid])
    return render_template('reply.html',view=query)

@mail.route('/replyaction',methods=['POST'])
def replyaction():
   sender=request.form['id']
   query=sql_query2("select * from message_tb where id=?",['id'])
   receiver=request.form['receivername']
   row=sql_query2("select * from register_tb where username=?",[receiver])
   receiverid=row[0][0]
   subject=request.form['subject']
   message=request.form['message']
   date=datetime.date.today()
   time=datetime.datetime.now().strftime("%H:%M")

   r=sql_edit_insert("insert into message_tb values(NULL,?,?,?,?,?,?,?)",(session['id'],receiverid,message,subject,date,time,'reply to msg')) 
   if r>0:
        msg="replied"
   else:
        msg="not replied"
   

   return redirect(url_for('inbox'))

@mail.route('/updateprofile')
def updateprofile():
    query=sql_query2("select * from register_tb where id=?",[session['id']])
    return render_template('updateprofile.html',view=query)

@mail.route('/updateprofileaction',methods=['POST'])
def updateprofileaction():
    id=request.form['id']
    name=request.form['name']
    address=request.form['address']
    gender=request.form['gender']
    country=request.form['country']
    phone=request.form['phone']
    username=request.form['username']
    password=request.form['password']

    query=sql_edit_insert("update register_tb set name=?,address=?,gender=?,country=?,phone=?,username=?,password=? where id=?",(name,address,gender,country,phone,username,password,id))
    return redirect(url_for('inbox'))

@mail.route('/country')
def country():
    query=sql_query("select * from country_tb")
    return render_template('country.html',country=query)

@mail.route('/getstate')
def getstate():
    state=request.args.get('country')
    query=sql_query2("select * from state_tb where countryid=?",[state])
    return render_template('getstate.html',states=query)

@mail.route('/addplace',methods=['POST'])
def addplace():
    country=request.form['country']
    state=request.form['state']
    place=request.form['place']
    query=sql_edit_insert("insert into place_tb values(NULL,?,?,?)",(country,state,place))
    return render_template('home.html')

@mail.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
if __name__== "__main__":
    mail.run(debug=True)
