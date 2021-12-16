//include modules
var AWS = require('aws-sdk'),
    fs = require('fs'),
    ts = require('tailstream'),
    exec = require('child_process').exec;
execSync = require('child_process').execSync;

// include IBM IoT library
var IoTClient = require('ibmiotf');
var config = {
    "org": "[your org]",
    "id": "[your device ID]",
    "domain": "internetofthings.ibmcloud.com",
    "type": "[your device type]",
    "auth-method": "token",
    "auth-token": "[your auth token]"
};
var WELCOME_SOUND = 'welcome.mpeg',
    commandReceived = false;

// IoT connection setup
var iotDeviceClient = new IoTClient.IotfDevice(config);
iotDeviceClient.connect();
iotDeviceClient.log.setLevel('trace');
// waiting for commands from other sensors and triggers the smart speaker
iotDeviceClient.on("command", function(commandName, format, payload, topic) {
    if (commandName === "ask" && !commandReceived) {
        console.log("ask command received");
        commandReceived = true;
        var playback = exec('mpg321 ' + WELCOME_SOUND);
        playback.on('close', function(code) {
            // smart speaker triggered by 'ask' command
            initiateFrailtyQStart();
        });

    } else if (commandReceived) {
        console.log("Command just received once");
    } else {
        console.log("Command not supported" + commandName);
    }
});
iotDeviceClient.on("error", function(err) {
    console.log("IoT error : " + err);
});

var FULFILLED = 'Fulfilled',
    FAILED = 'Failed',
    RESPONSE_FILE = 'response.mpeg',
    REMOVE_REQUEST_FILE = 'rm request.wav',
    SOX_COMMAND = 'sox -d -t wavpcm -c 1 -b 16 -r 16000 -e signed-integer --endian little - silence 1 0 1% 5 0.3t 2% > request.wav',
    streaming = false,
    inputStream,
    lexruntime = new AWS.LexRuntime({
        region: 'us-east-1',
        credentials: new AWS.Credentials(
            '[your AWS cred]',
            '[your AWS cred]', null)
    });

// initiate the smart speaker
var initiateFrailtyQStart = function() {
    var params = {
        botAlias: '$LATEST',
        botName: 'FrailtyToolkit',
        userId: 'testuser',
        accept: 'audio/mpeg',
        dialogAction: {
            type: 'Delegate',
            intentName: 'FrailtyQuestionsStart',    // feed intent to start a conversation
        }
    };

    lexruntime.putSession(params, function(err, data) {
        if (err) {
            console.log(err, err.stack);
            process.exit(1);
        } else {
            fs.writeFile(RESPONSE_FILE, data.audioStream, function(err) {
                if (err) {
                    return console.log(err);
                    process.exit(1);
                }
            });
            console.log(data);
            // play chatbot speech
            var playback = exec('mpg321 ' + RESPONSE_FILE);
            playback.on('close', function(code) {
                exec('rm ' + RESPONSE_FILE);
                if (data.dialogState !== FULFILLED) {
                    streaming = false;
                    // record user response
                    record();
                }
            });
        }
    });
}
// ask frailty question by feeding an intent name - each question is an intent

var askFrailtyQ = function(intentKeyword) {
    var params = {
        botAlias: '$LATEST',
        botName: 'FrailtyToolkit',
        userId: 'testuser',
        accept: 'audio/mpeg',
        dialogAction: {
            type: 'Delegate',
            intentName: intentKeyword,
        }
    };

    lexruntime.putSession(params, function(err, data) {
        if (err) {
            console.log(err, err.stack);
            process.exit(1);
        } else {
            fs.writeFile(RESPONSE_FILE, data.audioStream, function(err) {
                if (err) {
                    return console.log(err);
                    process.exit(1);
                }
            });
            console.log(data);
            // play chatbot audio
            var playback = exec('mpg321 ' + RESPONSE_FILE);
            playback.on('close', function(code) {
                exec('rm ' + RESPONSE_FILE);
                if (data.dialogState !== FULFILLED) {
                    streaming = false;
                    record();
                }
            });
        }
    });
}
// setup up conversation stream 
var setupStream = function() {
    streaming = true;
    inputStream = ts.createReadStream('./request.wav');
    var params = {
        botAlias: '$LATEST',
        botName: 'FrailtyToolkit',
        contentType: 'audio/l16; rate=16000; channels=1',
        inputStream: inputStream,
        userId: 'testuser',
        accept: 'audio/*',
    };

    lexruntime.postContent(params, function(err, data) {
        if (err) {
            console.log(err, err.stack);
            process.exit(1);
        } else {
            fs.writeFile(RESPONSE_FILE, data.audioStream, function(err) {
                if (err) {
                    return console.log(err);
                    process.exit(1);
                }
            });
            console.log(data);
            var playback = exec('mpg321 ' + RESPONSE_FILE);
            playback.on('close', function(code) {
                exec('rm ' + RESPONSE_FILE);
                exec(REMOVE_REQUEST_FILE);
                if (data.dialogState == FULFILLED || data.dialogState == FAILED) {
                    if (data.dialogState == FAILED) {
                        if (data.message === "No problem. I will ask at an another time.") {
                            streaming = true;
                        } else {
                            streaming = true;
                            // publish to IoT when users refuse to answer a question
                            iotDeviceClient.on('connect', function() {
                                // publishing user responses to IoT platform 
                                const str1 = '{"d" : { "isFatigue": ';
                                const str2 = String(data.sessionAttributes["isFatigue"]);
                                const str3 = '}}';
                                const combinedJSON = str1.concat('"').concat(str2).concat('"').concat(str3);
                                iotDeviceClient.publish("status", "json", combinedJSON);
                                console.log("publish successful");
                                iotDeviceClient.disconnect();
                            });
                        }
                        commandReceived = false;
                    } else if (data.intentName == "FrailtyQuestionsStart") {
                        console.log("start asking first Q");
                        askFrailtyQ("FrailtyFirstQuestion");
                        streaming = false;
                    } else if (data.intentName == "FrailtyFirstQuestion") {
                        console.log("start asking second Q");
                        askFrailtyQ("FrailtySecondQuestion");
                        streaming = false;

                    } else if (data.intentName == "FrailtySecondQuestion") {
                        streaming = true;
                        // publish to IoT when all questions were answered
                        iotDeviceClient.on('connect', function() {
                            // publishing full user responses to IoT platform
                            const str1 = '{"d" : { "isFatigue": ';
                            const str2 = data.sessionAttributes["isFatigue"];
                            const str3 = ', "frequency": '
                            const str4 = data.sessionAttributes["frequency"];
                            const str5 = '}}';
                            const combinedJSON2 = str1.concat('"').concat(str2).concat('"').concat(str3).concat('"').concat(str4).concat('"').concat(str5);
                            iotDeviceClient.publish("status", "json", combinedJSON2);
                            console.log("publish successful");
                            iotDeviceClient.disconnect();
                        });
                        console.log('done');
                        commandReceived = false;
                    }
                } else {
                    console.log("not fulfilled or failed ");
                    streaming = false;
                    record();
                    console.log(data);
                }
            });
        }
    });
}
// function for recording user response
var record = function() {
    console.log("start recording...");
    execSync(SOX_COMMAND);
    console.log("end recording...");
    if (!streaming) {
        setupStream();
    }
};