import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request, redirect, url_for

app = Flask(__name__)
#messageArgs = ["test", "invalid@gmail.com", "5.00"]

def format_input(message):
    params = message.split(",");
    for elem in params:
        elem = elem.strip()
    return params


@app.route('/', methods=['GET'])
def verify():
    print("Hello world")
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/redirect', methods=['GET'])
def hello_world():
    print(request.args.get("code"))
    params = {"client_id":"5633b82026504602837d70cf0a84323a",
        "grant_type": "authorization_code",
        "scope": "check",
        "code":request.args.get("code"),
        "redirect_uri": "https://checkbook-messenger-bot.herokuapp.com/redirect",
        "client_secret": "nWiQFp9iCGciZ8X1d62PTgNrosyXe3"}
    response = requests.post("https://sandbox.checkbook.io/oauth/token", params)
    #print(response.json());
    data = response.json()
    bearer_token = data["access_token"]

    url = "https://sandbox.checkbook.io/v3/check/digital"
    # body = messageArgs
    auth_header = 'bearer ' + bearer_token
    # print(body.json())
    # print(body)
    # headers = {
    #     'Content-Type': 'application/json',
    #     'Authorization': auth_header
    # }
    # response = requests.request("POST", url, data=body, headers=headers)
    # print(response.text)
    print("HERE3")
    data = read()
    messageArgs = format_input(data)
    print(messageArgs)
    body = '{\"name\":\"'+messageArgs[0]+'\",\"recipient\":\"'+messageArgs[1]+'\",\"amount\":'+messageArgs[2]+'}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth_header
    }
    response = requests.request("POST", url, data=body, headers=headers)
    print(response.text)
    send_message(messageArgs[3], "Your transaction is being processed. Check your email for conformation.")
    #send_message(sender_id, "You have successfully paid.")
    return redirect(url_for('success'))

@app.route('/success', methods=['GET'])
def success():
    return redirect("https://www.messenger.com")


@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    #name,email,amount
                    params = format_input(message_text)
                    if len(params) != 3 or "@" not in params[1] or "$" not in params[2]:
                        send_message(sender_id, "Please send message in the following format:")
                        send_message(sender_id, "\'Recipient Name\', \'Recipient Email\', \'$Payment\'")
                        return "ok", 200
                    string = ""
                    toEdit = params[2]
                    params[2] = toEdit[1:]
                    if len(params[2]) == 0:
                        send_message(sender_id, "Please enter a valid payment:")
                        send_message(sender_id, "\'Recipient Name\', \'Recipient Email\', \'$Payment\'")
                        return "ok", 200
                    for i in params:
                        string += i + " "
                    #formattedString = "{\"name\":" + "\"" + params[0] + "\"" + ",\"recipient\":" + "\"" + params[1] + "\"" + ",\"amount\":" + params[2] + "}"
                    #messageArgs = formattedString
                    #messageArgs = {'recipient': params[1], 'name': params[0], 'amount': params[2]}
                    print("HERE1")
                    write(params[0], params[1], params[2], sender_id)
                    print(params)
                    # messageArgs[0] = params[0]
                    # messageArgs[1] = params[1]
                    # messageArgs[2] = params[2]
                    print("HERE2")
                    #print(messageArgs)
                    #id = sender_id
                    send_message(sender_id, "Transaction of $" + params[2] + " to " + params[0] + "(" + params[1] + ")")

                    send_message(sender_id, "Please Authorize your Transaction: " )
                    send_message(sender_id,"https://sandbox.checkbook.io/oauth/authorize?client_id=5633b82026504602837d70cf0a84323a&response_type=code&scope=check&redirect_uri=https://checkbook-messenger-bot.herokuapp.com/redirect")

                    return "ok", 200


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)



def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    print(msg)

def write(name, email, amount, sender_id):
    file = open("data.txt", "w")
    file.write(name + "," + email + "," + amount + "," + sender_id)
    file.close()

def read():
    file = open("data.txt", "r")
    data = file.readlines()
    return data[0]


if __name__ == '__main__':
    app.run(debug=True)
