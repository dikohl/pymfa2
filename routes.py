#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Routes and views for the bottle application.
"""

import sys, os, hashlib, time, datetime
from bottle import route, view, request, response, redirect, os, static_file, abort
from runner_server import Runner

@route('/', method='GET')
@view('index')
def login():
    username = request.get_cookie("account", secret='abcdefg')
    if not username:
        #if response.status == 401:
        #    error = 'Username or Password incorrect'
        return dict(
            title='Login',
            error=''
        )
    else:
        return redirect("/upload")

@route('/', method='POST')
@view('index')
def login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    if(checkLogin(username, password)):
        response.set_cookie("account", username, secret='abcdefg')
        response.status = 303
        response.set_header('Location','/upload')
        return "success"
    else:
        #303 is not correct should be 401 (perhaps handle 401 abort)
        return dict(
            title='Login',
            error='Username or Password incorrect'
        )
        #return abort(401, "Wrong credentials")

@route('/upload', method='GET')
@view('upload')
def loginToUpload():
    #check cookie
    username = request.get_cookie("account", secret='abcdefg')
    if username:
        outputs = scanForOutputs()
        outWithDate = mapCreationDate(outputs)
        return dict(
            title='Upload',
            error='',
            outputs=outWithDate
        )
    else:
        #abort(401, "You need to login first")
        return redirect("/")

@route('/upload', method='POST')
@view('upload')
def upload():
    outputFile   = request.forms.get('outputFile')
    upload     = request.files.get('uploadFile')
    outputs = scanForOutputs()
    error, outputFile = checkAndFixFormData(outputFile,upload,outputs)
    if error is '':
        save_path = "input"
        
        #check inputs and see if file already exists
        #this is neccessary because if an error happens in the calculation the file won't be deleted
        checkInputDirectory(upload)
        #needs to be done here before new upload
        upload.save(save_path) # appends upload.filename automatically
        inputFile = save_path + "/" + upload.filename
        output = "outputs/" + outputFile
        runner = Runner(inputFile, output)
        error = runner.run()
        runner = None
        #delete the runner object
        outputs = scanForOutputs()
    outWithDate = mapCreationDate(outputs)
    return dict(
            title='Upload',
            error=error,
            outputs=outWithDate
        )

@route('/logout', method='POST')
def logout():
    if request.get_cookie("account", secret='abcdefg'):
        response.set_cookie("account", "dummy", secret='abcdefg', expires=0)
    return redirect("/")
    
@route('/download', method='POST')
def downloadFile():
    if request.get_cookie("account", secret='abcdefg'):
        outputs = scanForOutputs()
        output = request.forms.get('output')
        if output in outputs:
            return static_file(output, root='outputs', download=True)
        else:
            return '''
                This file does not exist anymore! Somebody must have deleted it.
                <form action="/upload" method="get">
                    <input type="submit" value="Ok"/>
                </form>
                '''
    else:
        return redirect("/")

@route('/delete', method='POST')
def deleteFile():
    if request.get_cookie("account", secret='abcdefg'):
        outputs = scanForOutputs()
        output = request.forms.get('output')
        if output in outputs:
            os.remove("outputs/" + output)
        return redirect("/upload")
    else:
        return redirect("/")

def checkLogin(username, password):
    #not secure, the user data should use a salt to hash and be stored in a database
    users = {
                "admin": "50bb61665eece21c7b70416f4ef139395052e09eb80721ed124b6370626c7d3d", 
                "user": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
            }
    hash = hashlib.sha256(password.encode('utf-8'))
    hex_dig = hash.hexdigest()
    if users.get(username) == hex_dig:
        return True
    else:
        return False

def scanForOutputs():
    outputs = [file for file in os.listdir("outputs") if file.endswith(".csv")]
    return outputs

def checkAndFixFormData(outputFile, upload, outputs):
    error = ''
    if not upload:
        error='You need to define a source'
    else:
        fileName, ext = os.path.splitext(upload.filename)
        if ext not in ('.csv'):
            error='CSV file needed as source'
            return error, outputFile
        if outputFile is '':
            outputFile = fileName + "_results.csv"
        elif not outputFile.endswith(".csv"):
            outputFile = outputFile + ".csv"
        if outputFile in outputs:
            error='Outputfile with this name already exists'
    return error, outputFile

def checkInputDirectory(upload):
    inputs = [file for file in os.listdir("input") if file.endswith(".csv")]
    if upload.filename in inputs:
        os.remove("input/" + upload.filename)
        
def mapCreationDate(outputs):
    outputsDate = dict()
    for output in outputs:
        date = time.ctime(os.path.getctime("outputs/" + output))
        date = datetime.datetime.strptime(date, "%a %b %d %H:%M:%S %Y")
        outputsDate[output] = date
    return outputsDate