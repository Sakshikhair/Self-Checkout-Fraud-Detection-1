import module
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import logging
import numpy as np
import pickle

app = Flask(__name__)
app.secret_key="checkout"
modelm=pickle.load(open('model1.pkl','rb'))


logging.basicConfig(filename='logs.log',level=logging.DEBUG,
format='%(asctime)s %(levelname)s %(name)s %(threadName)s  : %(message)s')

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Qwerty@13'
app.config['MYSQL_DB'] = 'typroject'

mysql = MySQL(app)


@app.route("/charts")
def charts():
    return render_template('charts.html')

@app.route("/features")
def features():
    return render_template('features.html')


@app.route("/home", methods=['POST','GET'])
def home():
    if request.method=='POST':
        trustLevel=request.form['trustLevel']
        totalScanTimeInSeconds=request.form['totalScanTimeInSeconds']
        grandTotal=request.form['grandTotal']
        lineItemVoids=request.form['lineItemVoids']
        grandTotal=request.form['grandTotal']
        scansWithoutRegistration=request.form['scansWithoutRegistration']
        quantityModifications=request.form['quantityModifications']
        scannedLineItemsPerSecond=request.form['scannedLineItemsPerSecond']
        valuePerSecond=request.form['valuePerSecond']
        lineItemVoidsPerPosition=request.form['lineItemVoidsPerPosition']
        

        session['trustLevel']=trustLevel
        session['totalScanTimeInSeconds']=totalScanTimeInSeconds
        session['grandTotal']=grandTotal
        session['lineItemVoids']=lineItemVoids
        session['scansWithoutRegistration']=scansWithoutRegistration
        session['quantityModifications']=quantityModifications
        session['scannedLineItemsPerSecond']=scannedLineItemsPerSecond
        session['valuePerSecond']=valuePerSecond
        session['lineItemVoidsPerPosition']=lineItemVoidsPerPosition
        return redirect(url_for('predict_m'))
    else:  
        return render_template('home.html')


@app.route('/prediction',methods=['GET', 'POST'])
def predict_m():
    session['totalScanned'] = float(session['scannedLineItemsPerSecond']) * float(session['totalScanTimeInSeconds'])
    # avgValuePerScan:
    session['avgTimePerScan'] = 1/ float(session['scannedLineItemsPerSecond'])
    session['avgValuePerScan'] = float(session['avgTimePerScan']) * float(session['valuePerSecond'])
    # manual feature generation - "totalScanned" ratios
    # withoutRegisPerPosition
    session['withoutRegisPerPosition'] = float(session['scansWithoutRegistration']) / float(session['totalScanned'])
    # ratio of scansWithoutRegis in totalScan
    # equivalent to lineItemVoidsPerPosition
    # Might indicate how new or ambivalent a customer is. Expected to be higher for low "trustLevel"
    # quantiModPerPosition
    session['quantiModPerPosition'] = float(session['quantityModifications']) / float(session['totalScanned'])
    # ratio of quanityMods in totalScan
    # manual feature generation - "grandTotal" ratios
    # lineItemVoidsPerTotal
    session['lineItemVoidsPerTotal'] = float(session['lineItemVoids']) / float(session['grandTotal'])

    # withoutRegisPerTotal
    session['withoutRegisPerTotal'] = float(session['scansWithoutRegistration']) / float(session['grandTotal'])
    # quantiModPerTotal
    session['quantiModPerTotal'] = float(session['quantityModifications']) / float(session['grandTotal'])
    # manual feature generation - "totalScanTimeInSeconds" ratios
    # lineItemVoidsPerTime
    session['lineItemVoidsPerTime'] = float(session['lineItemVoids']) / float(session['totalScanTimeInSeconds'])
    # withoutRegisPerTime
    session['withoutRegisPerTime'] = float(session['scansWithoutRegistration']) / float(session['totalScanTimeInSeconds'])
    # quantiModPerTime
    session['quantiModPerTime'] = float(session['quantityModifications']) / float(session['totalScanTimeInSeconds'])

    input_data=[session['trustLevel'], session['totalScanTimeInSeconds'], session['grandTotal'], session['lineItemVoids'],
       session['scansWithoutRegistration'], session['quantityModifications'],
       session['scannedLineItemsPerSecond'], session['valuePerSecond'],
       session['lineItemVoidsPerPosition'], session['totalScanned'], session['avgTimePerScan'],
       session['avgValuePerScan'], session['withoutRegisPerPosition'], session['quantiModPerPosition'],
       session['lineItemVoidsPerTotal'], session['withoutRegisPerTotal'], session['quantiModPerTotal'],
       session['lineItemVoidsPerTime'], session['withoutRegisPerTime'], session['quantiModPerTime']]
    input_data = np.asarray(input_data)
    input_data_reshaped = input_data.reshape(1,-1)
    prediction=modelm.predict(input_data_reshaped)

    if prediction[0]==0:
        reverb ='not fraud'
    else:
        reverb ='fraud'
    return render_template('prediction.html',predicts=reverb)


@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM selfcheckout WHERE username = % s AND password = % s', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return render_template('home.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))
  
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM selfcheckout WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO selfcheckout VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

if __name__ == "__main__":
    app.run(debug=True)