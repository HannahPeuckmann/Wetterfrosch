import logging
import requests # for http request 
import six
from datetime import datetime
from flask import Flask
from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractResponseInterceptor, AbstractRequestInterceptor)

from typing import Union, Dict, Any, List
from ask_sdk_model.dialog import (
    ElicitSlotDirective, DelegateDirective)
from ask_sdk_model import (
    Response, IntentRequest, DialogState, SlotConfirmationStatus, Slot)
from ask_sdk_model.slu.entityresolution import StatusCode

logging.basicConfig(filename='wetterfrosch_log.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s'
                    )

app = Flask(__name__)
sb = SkillBuilder()
# Register your intent handlers to the skill_builder object
# ---


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Willkommen bei Wetterfrosch, frag mich nach dem Wetter!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("wetter frosch", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response


class WetterIntentHandler(AbstractRequestHandler):
    """Handler for Wetter Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("WetterIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        filled_slots = handler_input.request_envelope.request.intent.slots
        slot_values = get_slot_values(filled_slots)
        ort = slot_values['ort']['resolved']
        zeit = slot_values['tag']['resolved']
        print(slot_values)
        if ort is None:
            ort = 'Berlin'
        if zeit is None:
            zeit = datetime.datetime.now().date()
        weather = build_url(api, api_key, ort)
        try:
            response = http_get(weather)
            if response["main"]:
                speech = ("Die Höchsttemperatur in {} liegt heute bei {} Grad."
                          " Die Mindesttemperatur liegt bei {} Grad."
                          " Gefühlt sind es {} Grad.".format(
                              response["name"],
                              int(response["main"]["temp_max"]),
                              int(response["main"]["temp_min"]),
                              int(response["main"]["feels_like"])))
        except Exception as e:
            speech = ('Tut mir leid, ich kann dir leider keine '
                      f'Informationen über das Wetter in {ort} geben')
            logging.info("Intent: {}: message: {}".format(
                handler_input.request_envelope.request.intent.name, str(e)))
        handler_input.response_builder.speak(speech).set_card(
            SimpleCard("wetter frosch", speech)).set_should_end_session(
                True)  # vorerst True
        return handler_input.response_builder.response

class SonnenuntergangIntentHandler(AbstractRequestHandler):
    """Handler for Temperatur Intent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        print(True)
        return is_intent_name("SonnenuntergangIntent")(handler_input)


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        filled_slots = handler_input.request_envelope.request.intent.slots
        slot_values = get_slot_values(filled_slots)
        ort = slot_values['ort']['resolved']
        zeit = slot_values['tag']['resolved']
        richtung = slot_values['sun']['resolved']
        time = None
        print(slot_values)
        if ort is None:
            ort = 'Berlin'
        if zeit is None:
            zeit = datetime.datetime.now().date()
        weather = build_url(api, api_key, ort)
        try:
            response = http_get(weather)
            print(response)
            if response["sys"]:
                print(response)
                if 'auf' in richtung:
                    richtung = 'Sonnenaufgang'
                    timestamp = response['sys']['sunrise']
                    date = datetime.fromtimestamp(timestamp)
                    time = date.time()
                    time = time.strftime("%H:%M:%S")
                else:
                    richtung = 'Sonnenuntergang'
                    timestamp = response['sys']['sunset']
                    date = datetime.fromtimestamp(timestamp)
                    time = date.time()
                    time = time.strftime("%H:%M:%S")
                speech = ('{} ist um {}'.format(richtung, time))
        except Exception as e:
            speech = ('Tut mir leid, ich kann dir leider keine '
                      f'Informationen über die gewünschten Daten in {ort} geben')
            logging.info("Intent: {}: message: {}".format(
                handler_input.request_envelope.request.intent.name, str(e)))
        handler_input.response_builder.speak(speech).set_card(
            SimpleCard("wetter frosch", speech)).set_should_end_session(
                True)  # vorerst True
        return handler_input.response_builder.response



class RegenIntentHandler(AbstractRequestHandler):
    """Handler for Regen Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("RegenIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        filled_slots = handler_input.request_envelope.request.intent.slots
        slot_values = get_slot_values(filled_slots)
        ort = slot_values['ort']['resolved']
        zeit = slot_values['tag']['resolved']
        print(slot_values)
        if ort is None:
            ort = 'Berlin'
        if zeit is None:
            zeit = datetime.datetime.now().date()
        weather = build_url(api, api_key, ort)
        try:
            response = http_get(weather)
            if response["weather"]:
                if response["weather"][0]['main'] == 'Rain':
                    speech = ('Heute regnet es in {}. '
                              'Die genaue Vorhersage lautet {}'.format(
                                  response["name"],
                                  response["weather"][0]['description']))
                else:
                    speech = ('Heute regnet es nicht in {}. '
                              'Die genaue Vorhersage lautet {}'.format(
                                  response["name"],
                                  response["weather"][0]['description']))
        except Exception as e:
            speech = ('Tut mir leid, ich kann dir leider keine '
                      f'Informationen über das Wetter in {ort} geben')
            logging.info("Intent: {}: message: {}".format(
                handler_input.request_envelope.request.intent.name, str(e)))
        handler_input.response_builder.speak(speech).set_card(
            SimpleCard("wetter frosch", speech)).set_should_end_session(
                True)  # vorerst True
        return handler_input.response_builder.response



class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Du kannst nach dem Wetter fragen"

        handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(
                "wetter frosch", speech_text))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Tschüss!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("wetter frosch", speech_text))
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = (
            "Wetterfrosch kann dir damit leider nicht helfen.")
        reprompt = "Du kannst mich zum Beispiel fagen, ob es heute regnen wird."
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


# Request and Response Loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""

    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logging.info("Request Envelope: {}".format(
            handler_input.request_envelope))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logging.info("Response: {}".format(response))


# Data

required_slots = ['ort', 'tag']
api = 'http://api.openweathermap.org/data/2.5/weather?q={}&lang=de&units=metric&APPID={}'
api_key = 'abc529c6c26889bfddf81f5a845be3fe'


# Utility functions
def get_resolved_value(request, slot_name):
    """Resolve the slot name from the request using resolutions."""
    # type: (IntentRequest, str) -> Union[str, None]
    try:
        return (request.intent.slots[slot_name].resolutions.
                resolutions_per_authority[0].values[0].value.name)
    except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
        logging.info("Couldn't resolve {} for request: {}".format(slot_name,
                                                                  request))
        logging.info(str(e))
        return None


def get_slot_values(filled_slots):
    """Return slot values with additional info."""
    # type: (Dict[str, Slot]) -> Dict[str, Any]
    slot_values = {}
    logging.info("Filled slots: {}".format(filled_slots))

    for key, slot_item in six.iteritems(filled_slots):
        name = slot_item.name
        try:
            status_code = slot_item.resolutions.resolutions_per_authority[0].status.code

            if status_code == StatusCode.ER_SUCCESS_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.resolutions.resolutions_per_authority[0].values[0].value.name,
                    "is_validated": True,
                }
            elif status_code == StatusCode.ER_SUCCESS_NO_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.value,
                    "is_validated": False,
                }
            else:
                pass
        except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
            logging.info("Couldn't resolve status_code for slot item: {}".format(slot_item))
            logging.info(e)
            slot_values[name] = {
                "synonym": slot_item.value,
                "resolved": slot_item.value,
                "is_validated": False,
            }
    return slot_values


def build_url(api, key, location):
    """Return options for HTTP Get call."""
    url = api.format(location, key)
    return url


def http_get(url):
    response = requests.get(url)
    print(url)

    if response.status_code < 200 or response.status_code >= 300:
        response.raise_for_status()

    return response.json()


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(WetterIntentHandler())
sb.add_request_handler(RegenIntentHandler())
sb.add_request_handler(SonnenuntergangIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())


# ---
skill_adapter = SkillAdapter(
    skill=sb.create(), skill_id='TEST', app=app)


@app.route("/", methods=['POST'])
def invoke_skill():
    return skill_adapter.dispatch_request()


if __name__ == '__main__':
    app.run(debug=True)
