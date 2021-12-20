import wiotp.sdk.application
import time
import json

myConfig = wiotp.sdk.application.parseConfigFile("application.yaml")

client = wiotp.sdk.application.ApplicationClient(config=myConfig, logHandlers=None)

def myCommandCallback(cmd):
    print("Command received: %s" % cmd.data)

client.commandCallback = myCommandCallback

def myEventCallback(event):
        str = "%s event '%s' received from device [%s]: %s"
        print(str % (event.format, event.eventId, event.device, json.dumps(event.data)))
        #publish a command to speaker to trigger speaker to initiate questioning process
        commandData={'ask' : 1}
        client.publishCommand("speaker", "speaker001", "ask", "json", commandData)
        print("Command 'ask' published")

client.connect()
client.deviceEventCallback = myEventCallback
client.subscribeToDeviceEvents(typeId='motion_sensor')

#keep the script running for subscription
while True:
        time.sleep(1)
