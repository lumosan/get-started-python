from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify
import atexit
import cf_deployment_tracker
import os
import json
from watson_developer_cloud import LanguageTranslatorV2
from watson_developer_cloud import TextToSpeechV1
from os.path import join, dirname

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

db_name = 'mydb_trans'
client = None
db = None
language_translator = None
text_to_speech = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

        creds2 = vcap['language_translator'][0]['credentials']
        user2 = creds2['username']
        password2 = creds2['password']
        url2 = creds2['url']
        language_translator = LanguageTranslatorV2(
            username=user2, password=password2, url=url2)

        creds3 = vcap['services']['text_to_speech'][0]['credentials']
        user3 = creds3['username']
        password3 = creds3['password']
        text_to_speech = TextToSpeechV1(username=user3,
            password=password3)  # Optional flag

elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
        
        print(vcap.keys())

        creds2 = vcap['services']['language_translator'][0]['credentials']
        user2 = creds2['username']
        password2 = creds2['password']
        url2 = creds2['url']
        language_translator = LanguageTranslatorV2(
                        username=user2, password=password2)


        creds3 = vcap['services']['text_to_speech'][0]['credentials']
        user3 = creds3['username']
        password3 = creds3['password']
        text_to_speech = TextToSpeechV1(username=user3,
            password=password3)  # Optional flag

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('PORT', 8080))

@app.route('/')
def home():
    return render_template('index.html')

# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8080/api/visitors with body
# * {
# *     "name": "Bob"
# * }
# */
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:
        return jsonify(list(map(lambda doc: doc['name'], db)))
    else:
        print('Sin base de datos')
        return jsonify([])

# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8080/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */
@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    if client:
        trans = language_translator.translate(user, source='es', target='en')
        data = {'name':trans}
        db.create_document(data)
        text_to_speech.synthesize(trans, accept='audio/wav',
                                           voice="en-US_AllisonVoice")#)
        return 'Se ha guardado "%s" en la base de datos' % user
    else:
        print('Sin base de datos')
        return 'Hello %s!' % user

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
