#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Routes and views for the bottle application.
"""

import sys, os, hashlib, time, datetime
from bottle import route, view, request, response, redirect, os, static_file, abort
from runner_server import Runner
import shutil


#first view of the website
@route('/', method='GET')
@view('index')
def login():
    #check if there is already a cookie
    username = request.get_cookie("account", secret='abcdefg')
    if not username:
        #return the login screen
        return dict(
            title='Login',
            error=''
        )
    else:
        #redirect the user to the upload view
        return redirect("/upload")

#this route is used to check the login credentials and create a cookie if they are correct
@route('/', method='POST')
@view('index')
def login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    if(checkLogin(username, password)):
        #if the credentials are correct, create cookie and redirect the user to the uplaod view
        response.set_cookie("account", username, secret='abcdefg')
        response.status = 303
        response.set_header('Location','/upload')
        return "success"
    else:
        #if the credentials are wrong show an error on the first view
        return dict(
            title='Login',
            error='Username or Password incorrect'
        )

#this route shows logged in users all the uploaded analyses and gives the option to upload a file
@route('/upload', method='GET')
@view('upload')
def loginToUpload():
    #check cookie
    username = request.get_cookie("account", secret='abcdefg')
    if username:
        #get all analyses
        outputs = scanForOutputs()
        outWithDate = mapCreationDate(outputs)
        #show the view with a list of analyses
        return dict(
            title='Upload',
            error='',
            outputs=outWithDate
        )
    else:
        #if there is no cookie redirect the user to the login view
        return redirect("/")

#this route handles the upload of a file
@route('/upload', method='POST')
@view('upload')
def upload():
    #get the outputFile name and the uploaded file
    outputFile = request.forms.get('outputFile')
    upload = request.files.get('uploadFile')
    outputs = scanForOutputs()
    #check and fix the form of the outputFile name
    error, outputFile = checkAndFixFormData(outputFile,upload)
    #if the outputFile name is accepted
    if error is '':
        #get current time and create a folder with that name
        creationTime = datetime.datetime.strftime(datetime.datetime.now(), '%d-%m-%Y_%H+%M+%S')
        save_path = 'analysis/' + creationTime
        os.makedirs(save_path + "/out")
        
        #save the uploaded file to the directory
        upload.save(save_path) #appends upload.filename automatically
        inputFile = save_path + "/" + upload.filename
        output = save_path + "/" + outputFile
        
        #start the runner, this starts the analysis
        runner = Runner(inputFile, output)
        error = runner.run()
        #delete the runner object
        runner = None
        #get the new list of available analyses
        outputs = scanForOutputs()
    outWithDate = mapCreationDate(outputs)
    #show the updated upload view
    return dict(
            title='Upload',
            error=error,
            outputs=outWithDate
        )

#this route handles the logout
@route('/logout', method='POST')
def logout():
    #the cookie expiration time is set to 0 so it gets deleted
    if request.get_cookie("account", secret='abcdefg'):
        response.set_cookie("account", "dummy", secret='abcdefg', expires=0)
    return redirect("/")
    
#the download route handles the download of files
@route('/download', method='POST')
def downloadFile():
    #check if user is logged in
    if request.get_cookie("account", secret='abcdefg'):
        #get filename and date form the form
        output = request.forms.get('output')
        date = request.forms.get('date')
        #replace the : with + so the filesystem can handle the name
        date = date.replace(':', '+')
        
        #if the source should be downloaded
        if output == 'source':
            for root, dirs, files in os.walk('analysis/'+date):
                for f in files:
                    if f[-4:] == '.csv':
                        return static_file(date+'/'+f, root='analysis', download=True)
            return '''
                This file does not exist anymore! Somebody must have deleted it.
                <form action="/upload" method="get">
                    <input type="submit" value="Ok"/>
                </form>
                '''
        if output == 'plots':
            for root, dirs, files in os.walk('analysis/'+date+'plots'):
                for f in files:
                    if f == 'plots.zip':
                        return static_file(date+"/"+f, root='analysis', download=True)
            else:
                return '''
                    This analysis does not have any plots.
                    <form action="/upload" method="get">
                        <input type="submit" value="Ok"/>
                    </form>
                    '''

        ''''#check if it is a duplicate outputFile name
        if output[-1] == ')':
            #if so get rid of the number (everything after .csv)
            output = output[0:output.find('.csv')+4]'''
        #create the full path to the outputfile
        download = date + "/" + "out/" + output
        #check if file is still there
        outputs = scanForOutputs()
        if download in outputs:
            #give the user the download
            return static_file(download, root='analysis', download=True)
        else:
            #if it is not there anymore, show an error message
            return '''
                This file does not exist anymore! Somebody must have deleted it.
                <form action="/upload" method="get">
                    <input type="submit" value="Ok"/>
                </form>
                '''
    #if the user is not logged in, redirect to login page
    else:
        return redirect("/")

#this route deletes files
@route('/delete', method='POST')
def deleteFile():
    #check if user is logged in
    if request.get_cookie("account", secret='abcdefg'):
        #get the name of the folder that should be deleted
        date = request.forms.get('date')
        date = date.replace(':', '+')
        #delete directory
        shutil.rmtree('analysis/' + date)
        #redirect to the updated upload view
        return redirect("/upload")
    #if not redirect to login view
    else:
        return redirect("/")

#method to check the login credentials of the user
def checkLogin(username, password):
    #not secure, the user data should use a salt to hash and be stored in a database
    #the passwords are hashed so we don't save them in clear text
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

#find all the analyses
def scanForOutputs():
    outputs = []
    #scan the directory
    for root, dirs, files in os.walk('analysis'):
        folder, date = os.path.split(root)
        for root, dirs, files in os.walk(root + '/out'):
            for f in files:
                outputs.append(os.path.join(date,"out",f))
    return outputs

#check the uploaded file and fix the outputFile name
def checkAndFixFormData(outputFile, upload):
    error = ''
    if not upload:
        error='You need to define a source'
    else:
        #check if there is a .csv at the end of upload file
        fileName, ext = os.path.splitext(upload.filename)
        if ext not in ('.csv'):
            error='CSV file needed as source'
            return error, outputFile
        #fix the outputFile name if it's the same as the input file
        if outputFile is '' or outputFile.split('.')[0] == fileName:
            outputFile = fileName + "_results.csv"
        #fix the outputFile name if it does not end in .csv
        elif not outputFile.endswith(".csv"):
            outputFile = outputFile + ".csv"
    return error, "out/"+outputFile
        
#maps the creation date to the output files
def mapCreationDate(outputs):
    outputsDate = []
    for output in outputs:
        #split filename from folder name
        date = []
        try:
           date_list_out, file = os.path.split(output)
           date_list, out = os.path.split(date_list_out)
        except ValueError:
           print("Could not split output: " +output)
           continue
        date.append(date_list)
        #format the folder name so we get a proper date
        real_date = date[0].replace('+', ':')
        #if there are multiple output files with the same name append numbers to them
        '''if out in keys:
            i = 1
            while out+" (" +str(i)+ ")" in keys:
                i += 1
            outputsDate[out+" (" +str(i)+ ")"] = real_date
        else:
            #fill dictionary with outputname:creationDate
            outputsDate[out] = real_date'''
        
        outputsDate.append((file,real_date))
    return list(reversed(outputsDate))