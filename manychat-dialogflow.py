'''
    This code is a bridge between ManyChat and DialogFlow.
    You can use it to handle the text inputs that ManyChat do not understand with DialogFlow.
    Upload the code to your server and run it as a Flask app.
    Set a virtual environment variable named GOOGLE_APPLICATION_CREDENTIALS and point it to your DialogFlow JSON credential file.
    If you do not want to use a virtual environment variable, then set the service_account_json when creating DialogFlow object.
    Get the URL to it and set it as dynamic response in your default reply inside ManyChat.
    Set your DialogFlow intent's responses to text or custom payload and use {"flow": "flow_id"} to call an specific flow.
    Enjoy!

    YOUTUBE VIDEO: https://www.youtube.com/watch?v=6AA7NW3-LfQ
    Notes:
    I can't provide support to this code, you need to install it, run and set it up by yourself.
    If you need help to install it on your own server or want me to host it for you,
    please contact me and I will be happy to help for a fairly price.
    Author: Daian Gan
    Email: daian@ganmedia.com
    Website: https://ganmedia.com/
    Messenger: https://m.me/ganmedia/
'''

import json

import dialogflow_v2 as dialogflow
import requests
from flask import Flask, request
from google.protobuf import json_format

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def dialogflow_manychat_bridge():
    if request.method == 'POST':

        manychat_data = request.get_json()

        psid = manychat_data['id']
        last_input_text = manychat_data['last_input_text']
        locale = manychat_data['locale']
        language_code = locale.split('_')[0]
        if 'language_code' in manychat_data['custom_fields']:
            language_code = manychat_data['custom_fields']['language_code']

        df = DialogFlow(
            project_id='YOUR_DIALOGFLOW_PROJECT_ID',

            # Avoid calling the json credentials here in code and instead
            # use a virtual environment variable named GOOGLE_APPLICATION_CREDENTIALS.
            # If you do not want to use the virtual environment variable, please uncomment the following line:
            service_account_json='./config.json',
        )

        manychat_api_key = 'FILL_IN_YOUR_MANYCHAT_API_KEY'
        mc = ManyChat(
            api_key=manychat_api_key,
            psid=psid,
        )

        dialogflow_response = df.detect_intent(
            session_id=f'{psid}',
            texts=[
                last_input_text,
            ],
            language_code=language_code,
        )

        dialogflow_response_dict = json_format.MessageToDict(dialogflow_response)
        if dialogflow_response_dict['queryResult']['parameters']:
            for key, value in dialogflow_response_dict['queryResult']['parameters'].items():
                if value and value != '':
                    mc.set_manychat_user_custom_field_by_name(
                        field_name=key,
                        field_value=value[0] if isinstance(value, list) else value,
                    )

        for message in dialogflow_response.query_result.fulfillment_messages:
            if message.text.text:
                mc.send_manychat_content(
                    messages=[message.text.text[0]]
                )

            if len(message.payload.fields.items()) > 0:
                for key, value in message.payload.fields.items():

                    if key == 'flow':
                        mc.send_manychat_flow(
                            flow_ns=value.string_value,
                        )

        response = {
            'version': 'v2',
            'content': {
                'messages': []
            }
        }
        return response


    else:
        return 'Method not allowed'


class ManyChat:
    api_base_url = 'https://api.manychat.com/fb/'

    def __init__(self, api_key, psid):
        self.api_key = api_key
        self.psid = psid
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }

    def send_manychat_content(self, messages: list):
        params = {
            'subscriber_id': self.psid,
            'data': {
                'version': 'v2',
                'content': {
                    'messages': [
                        {
                            'type': 'text',
                            'text': message,
                        } for message in messages
                    ]
                }
            },
            'message_tag': 'ACCOUNT_UPDATE'
        }

        response = requests.post(
            url=f'{self.api_base_url}sending/sendContent',
            headers=self.headers,
            data=json.dumps(params)
        )

        results = json.loads(response.text)

        return results

    def send_manychat_flow(self, flow_ns):
        params = {
            'subscriber_id': self.psid,
            'flow_ns': flow_ns,
        }

        response = requests.post(
            url=f'{self.api_base_url}sending/sendFlow',
            headers=self.headers,
            data=json.dumps(params)
        )

        results = json.loads(response.text)

        return results

    def set_manychat_user_custom_field_by_name(self, field_name, field_value):
        params = {
            'subscriber_id': self.psid,
            'field_name': field_name,
            'field_value': field_value,
        }

        response = requests.post(
            url=f'{self.api_base_url}subscriber/setCustomFieldByName',
            headers=self.headers,
            data=json.dumps(params)
        )

        results = json.loads(response.text)

        print(json.dumps(results, indent=4, sort_keys=True))

        return results


class DialogFlow:

    def __init__(self, project_id: str = '', service_account_json: str = None):
        self.project_id = project_id
        self.service_account_json = service_account_json

    def detect_intent(self, session_id, texts, language_code):
        if self.service_account_json:
            session_client = dialogflow.SessionsClient.from_service_account_json(self.service_account_json)

        else:
            session_client = dialogflow.SessionsClient()

        session = session_client.session_path(self.project_id, session_id)

        for text in texts:
            text_input = dialogflow.types.TextInput(
                text=text,
                language_code=language_code
            )

            query_input = dialogflow.types.QueryInput(
                text=text_input
            )

            response = session_client.detect_intent(
                session=session,
                query_input=query_input
            )

            return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
