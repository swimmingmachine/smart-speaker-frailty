"""
This program demonstrates an implementation of the Lex Code Hook Interface
in order to serve a chatbot which manages conversation for collecting self-report exhaustion data in frailty assessment.
Bot, Intent, and Slot models which are compatible with this program can be setup in the AWS Lex Console.

"""

import json
import datetime
import time
import os
import dateutil.parser
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def elicit_intent(session_attributes, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitIntent',
            "message": {
                "contentType": "PlainText",
                "content": message
            }
        }
    }

def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, intentName, agreeVar, confirmation_status, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'recentIntentSummaryView':[
            {
                "intentName": intentName,
                "slots": {
                    "agreeTest": 'no',
                    "isFatigue": 'yes',
                    "frequency": 'rare'
                },
                "confirmationStatus": confirmation_status,
                "dialogActionType": "Close",
                "fulfillmentState": "Fulfilled"
            }
        ],
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---

def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None

""" --- Functions that control the bot's behavior --- """

def frailty_questions_start(intent_request):
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    #dialog_state = intent_request['currentIntent']['dialogState']
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        session_attributes['confirmation_status'] = confirmation_status
        if confirmation_status == 'None':
            return delegate(session_attributes, intent_request['currentIntent']['slots'])
        if confirmation_status == 'Confirmed':
            return close(
                session_attributes,
                'Fulfilled',
                {
                    'contentType': 'PlainText',
                    'content': "Alright, let's start."
                }
            )
        if confirmation_status == 'Denied':
            return close(
                session_attributes,
                'Failed',
                {
                    'contentType': 'PlainText',
                    'content': "No problem. I will ask at an another time. "
                }
            )

def frailty_first_question(intent_request):
    slots = intent_request['currentIntent']['slots']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    session_attributes['isFatigue'] = 'None'

    if intent_request['invocationSource'] == 'DialogCodeHook':
        session_attributes['confirmation_status'] = confirmation_status
        if confirmation_status == 'None':
            return delegate(session_attributes, intent_request['currentIntent']['slots'])
        if confirmation_status == 'Confirmed':
            session_attributes['isFatigue'] = 'yes'
            return close(
                session_attributes,
                'Fulfilled',
                {
                    'contentType': 'PlainText',
                    'content': "OK, got it. Next question. "
                }
            )
        if confirmation_status == 'Denied':
            session_attributes['isFatigue'] = 'no'
            try_ex(lambda: session_attributes.pop('confirmation_status'))
            return delegate(session_attributes, intent_request['currentIntent']['slots'])

def frailty_second_question(intent_request):
    slots = intent_request['currentIntent']['slots']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    session_attributes['frequency'] = 'None'

    if intent_request['invocationSource'] == 'DialogCodeHook':
        if slots['frequency'] != None:
            session_attributes['frequency'] = slots['frequency']
            return close(
                session_attributes,
                'Fulfilled',
                {
                    'contentType': 'PlainText',
                    'content': 'You have completed the frailty test. Thank you. Talk to you soon. '
                }
            )
    return delegate(session_attributes, intent_request['currentIntent']['slots'])

def agree_intent(intent_request):
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

# --- Intents ---

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'AgreeIntent':
        return answer_question(intent_request)
    elif intent_name == 'FrailtyFirstQuestion':
        return frailty_first_question(intent_request)
    elif intent_name == 'FrailtySecondQuestion':
        return frailty_second_question(intent_request)
    elif intent_name == 'FrailtyQuestionsStart':
        return frailty_questions_start(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')

# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
