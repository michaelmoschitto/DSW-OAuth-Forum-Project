from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template

import pprint
import os
import json

app = Flask(__name__)

app.debug = True #Change this to False for production
jsonData="post.json"

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)



#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#use a JSON file to store the past posts.  A global list variable doesn't work when handling multiple requests coming in and being handled on different threads
#Create and set a global variable for the name of you JSON file here.  The file will be created on Heroku, so you don't need to make it in GitHub

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():

    with open(jsonData) as myjson:
        myFile = json.load(myjson)
    return render_template('home.html', past_posts=posts_to_html())
    # return render_template('home.html')

#fixes the error no file or directory for my json file
os.system("echo '[]'>" + jsonData)
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def posts_to_html():
    table = Markup("<table class='table table-bordered'> <tr> <th> Username </th> <th> Message </th> </tr>")
    try:
        with open(jsonData, 'r+') as j:
            postData=json.load(j)

        for i in postData:
            table += Markup("<tr> <td>" + i["username"] + "</td> <td>" + i["message"] + "</td>" + "<td>" + '<button type="button" class="btn btn-secondary">Secondary</button>' + "</td>" + "</tr>")
            # + "<td>" + "<button type="button" class="btn btn-secondary">Secondary</button>" + "</td>")
    except:
        table += Markup("</table>")
    return table

@app.route('/posted', methods=['POST'])
def post():
    username=session['user_data']['login']
    postText=request.form['message']
    # if postText="":
        # return render_template('message.html', message='Message needs to contain text')
    try:
        with open(jsonData, 'r+') as j:
            postData=json.load(j)
            # add new post to the list. Delete everything from the json file and put in list
            postData.append({"username":username, "message":postText})

            j.seek(0)
            j.truncate()
            json.dump(postData,j)
            print(postData)
    except Exception as e:
        print("unable to load Json")
        print(e)

    return render_template('home.html', past_posts=posts_to_html())
    #This function should add the new post to the JSON file of posts and then render home.html and display the posts.
    #Every post should include the username of the poster and text of the post.

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():
    # session.clear()
    return github.authorize(callback='https://forum-oath-project.herokuapp.com/login/authorized') #callback URL must match the pre-configured callback URL

    # (callback=url_for('authorized', _external=True, _scheme='https'))

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        # session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run()
