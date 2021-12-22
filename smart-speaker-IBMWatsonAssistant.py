import json
import sys
import time
from time import sleep
import datetime
import os
from os.path import join, dirname
sys.path.append(os.path.join(os.getcwd(),'..','..'))
import watson_developer_cloud
from watson_developer_cloud import SpeechToTextV1 as SpeechToText
import requests
import logging
import logging.config
import argparse

#For Record and Play audio
import pyaudio
import wave
from array import array
from struct import pack
from sys import byteorder

#For Camera
import picamera

#For IoTP
try:
    print("importing ibmiotf.device")
    import ibmiotf.device as iotdevice

except ImportError:
    print("unable to import ibmiotf")
    sys.exit()


#Conversation Service
WatsonAssistantUSERNAME = os.environ.get('CONVERSATION_USERNAME','apikey')
WatsonAssistantPASSWORD = os.environ.get('CONVERSATION_PASSWORD','your conv password')

conversation = watson_developer_cloud.ConversationV1(username=WatsonAssistantUSERNAME, password=WatsonAssistantPASSWORD, version='2017-04-21')

workspace_id ='your work space id'
workspace = conversation.get_workspace(workspace_id=workspace_id, export=True)

#Text To Speech
TextSpeechUSERNAME = os.environ.get('TextSpeech_USERNAME','your text to speech username')
TextSpeechPASSWORD = os.environ.get('TextSpeech_PASSWORD','your password')

text_to_speech = watson_developer_cloud.TextToSpeechV1(username=TextSpeechUSERNAME, password=TextSpeechPASSWORD)

#Speech To Text
SpeechTextUSERNAME = os.environ.get('SpeechText_USERNAME','your speech to text username')
SpeechTextPASSWORD = os.environ.get('SpeechText_PASSWORD','your password')

speech_to_text = watson_developer_cloud.SpeechToTextV1(username=SpeechTextUSERNAME, password=SpeechTextPASSWORD)

#Camera Module
#camera = picamera.PiCamera()
#url = 'https://gateway-a.watsonplatform.net/visual-recognition/api/v3/classify?api_key=959331b8d0af7b3c1e21d58543af5e22f17b3ace&version=2016-05-20'


# check workspace status (wait for training to complete)
print('The workspace status is: {0}'.format(workspace['status']))
if workspace['status'] == 'Available':
    print('Ready to chat!')
else:
    print('The workspace should be available shortly. Please try again in 30s.')
    print('(You can send messages, but not all functionality will be supported yet.)')


def setup_logging(
        default_path='/home/pi/logging.json',
        default_level=logging.DEBUG
):
    path = default_path
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

def publishCallback():
    logger.info("Publish successful")
    
#Play audio
def playWaveAudio(filename):
    #Play the wave file
    CHUNK = 1024
    wf = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)

    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()
    p.terminate()

#Record audio
def recordWaveAudio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "input.wav"

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, 
                    channels=CHANNELS, 
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


#Get the user's input
def promptMessage(question):
    # Text to Speech
    # Generate the wave audio file
    fileName = 'output.wav'
    filePath = './audio/' + fileName

    with open(join(dirname(__file__), filePath),'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(question, accept='audio/wav',
                                  voice="en-US_MichaelVoice").content)
                                       
    #Play the wave audio file
    playWaveAudio(filePath)
    
    #Catch user's input
    # recordfile = raw_input() 
    print("please speak a word into the microphone")
    recordWaveAudio()
    print("done - result written to input.wav")
    
    #Speech to Text
    #Recognize the wave audio file
    inputFileName = 'input.wav'
    inputFilePath = './audio/' + inputFileName

    with open(join(dirname(__file__), inputFilePath), 'rb') as audio_file:
        results = speech_to_text.recognize(
                        #model='zh-CN_BroadbandModel',
                        audio=audio_file,
                        content_type='audio/wav',
                        timestamps=True,
                        word_confidence=True)

    # print(json.dumps(results['results'][0]['alternatives'][0]['transcript']))  
    # print(json.dumps(results['results']))

    recordfile= ''
    for i in range (0, len(results['results'])):
            if len(results['results'][i]) > 0:
                recordfile = results['results'][i]['alternatives'][0]['transcript']
                print(recordfile)
            else: 
                recordfile= ''

    return recordfile


#Main Conversation Function
def convMessage(message, context1):
    try:
        #Set conversation context
        input_content = {'text': message}
        
        #Send message to Waston Assistant to deal with
        response = conversation.message(workspace_id=workspace_id,input=input_content, context=context1)

        results = ''
        #Get the Watson's output results
        for i in range (0, len(response['output']['text'])):
           if len(response['output']['text'][i]) > 0:
               results = results + response['output']['text'][i] + ' '
               
        if len(results) > 0:
            userAnswer = promptMessage(results)     
            convMessage(userAnswer,response['context'])   
    except Exception as e:
        print('Exceptions: %s' % e)                   
    
#Image Analysis Function
def image_analysis():
    # send photo to visual recognition
    files = {'image.jpg': open('/home/pi/image.jpg', 'rb')}
    response = requests.post(url, files=files)
    #print(response.json())

    #find face in jason
    human_classes = ["thumb", "skin", "person"]
    data = response.json()
    classes = data['images'][0]['classifiers'][0]['classes']
    for c in classes:
        if c['class'] in human_classes:
            print("human detected...")
            return True
    print("No human activities...")
    return False

def main():
    #IoT Platform
    authMethod = None
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--organization', required=False, default='your org id')
    parser.add_argument('-T', '--deviceType', required=False, default='PI_3')
    parser.add_argument('-I', '--deviceId', required=False, default='iot-edge-01')
    parser.add_argument('-t', '--token', required=False, default='your auth token')
    parser.add_argument('-c', '--cfg', required=False, default=None)
    parser.add_argument('-E', '--event', required=False, default='status')
    parser.add_argument('-N', '--nummsgs', required=False, default=999999)
    parser.add_argument('-D', '--delay', required=False, default=1)
    parser.add_argument('-P', '--pin', required=False, default=4)
    args, unknown = parser.parse_known_args()
    logger.info('setup is completed...')

    if args.token:
        authMethod = "token"
    while True:
        try:
            if args.cfg is not None:
                deviceOptions = iotdevice.ParseConfigFile(args.cfg)
            else:
                deviceOptions = {"org": args.organization,
                                    "type": args.deviceType,
                                    "id": args.deviceId,
                                    "auth-method": authMethod,
                                    "auth-token": args.token}

            logger.info("deviceOptions: %s" % str(deviceOptions))
            # Connect to Watson IoT platform and send data into the cloud
            device = iotdevice.Client(deviceOptions)
            # Setup callback function for receiving command callback
            #device.commandCallback = commandProcessor

            # Connect device to IoT platform
            device.connect()
            logger.info("device connected")

        except iotdevice.ConnectionException:
            logger.exception("watson iot connection error retry in 10s")
            sleep(10)
            continue

        except Exception as e:
            logger.exception("device connection error and retry in 10s")
            sleep(10)
            continue
        break

    # publish an init message
    curTime = datetime.datetime.now()
    curTimeStr = curTime.strftime("%Y-%m-%d %H:%M:%S")
    data = {"d": {args.event: 'success',
                    'timestamp': curTimeStr,
                    'reset': True}}

    logger.info("PUBLISH: data: %s" % str(data))
    result = device.publishEvent(args.event, "json", data, qos=0, on_publish=publishCallback)
    logger.info("PUBLISH: result = %s" % str(result))


    while True:
        #For every 3 seconds to take a pic
        time.sleep(10)
        print("taking a picture...")    
        camera.capture("/home/pi/image.jpg", use_video_port=True)
        
        #Analyze the pic
        print("analyzing the picture...")    
        blnDetectHuman = image_analysis()

        if blnDetectHuman:
            # publish IoT event
            curTime = datetime.datetime.now()
            curTimeStr = curTime.strftime("%Y-%m-%d %H:%M:%S")
            data = {"d": {args.event: 'success',
                            'timestamp': curTimeStr,
                            'activity': 1}}

            logger.info("PUBLISH: data: %s" % str(data))
            result = device.publishEvent(args.event, "json", data, qos=0, on_publish=publishCallback)
            logger.info("PUBLISH: result = %s" % str(result))

            #Initialize the conversation
            response = conversation.message(
                workspace_id=workspace_id,
                input={
                    'text': ''
                }
            )
            #Initialize the context
            context = response['context']

            #Get the Watson's output results
            results = response['output']['text'][0]

            if len(results) > 0:
                #Get the user's input
                userAnswer = promptMessage(results)     

                #Call main conversation message function
                convMessage(userAnswer,context)

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.info("load logger config file")
    setup_logging(default_path='/home/pi/logging.json', default_level=logging.DEBUG)

    main()





