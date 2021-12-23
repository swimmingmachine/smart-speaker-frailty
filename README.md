# A customized smart speaker for self-report data collection for fraitly assessment in home settings

## Design and development
The smart speaker comprised a speaker, a voice accessory expansion board, a 6-mics circular array board, and a micro-computer. The 6-mics array board allows omnidirec-tional voice capture. The micro-computer was a Raspberry Pi, which has more computing power than the Arduino-based micro-controllers of other sensors to process complicated tasks. A representative smart speaker is illustrated in the figure below. 

![Hardware components and wiring of a typical smart speaker](https://user-images.githubusercontent.com/50496048/146663792-e93269bf-f047-4d51-9dae-040bf41c565b.png)


Self-report exhaustion is one of the essential frailty criteria in clinical frailty assessment. We programmed a smart speaker to ask the questions from the Center for Epidemiologic Studies Depression Scale (CES–D) to collect data about self-report exhaustion defined in Fried’s phenotype model. The speaker asked the following two questions sequentially,
* “Do you feel that everything you did was an effort?”
* “How often in the last week did you feel this way?”

While the first question is a yes or no question, the second question expects users to answer one of the three words, “always”, “sometimes”, or “rare”. Users responding “sometimes” or “always” will be categorized as frail for this criterion. A sample interaction between the smart speaker and a user is as illustrated in the following figure.
 
![AWS lex conversation sample](https://user-images.githubusercontent.com/50496048/146663643-e91a0084-6e61-4343-bb5f-819ab57b13f1.png)

The AWS Lex was used to build a chatbot to handle the user conversation. The IBM Watson IoT platform was used to receive user responses from the smart speaker.

## Deployment
The smart speaker was deployed and tested in [HomeLab](https://kite-uhn.com/lab/homelab) at [KITE Research](https://kite-uhn.com/), Toronto Rehabilitation Institute, Toronto, Canada. It could be placed in a convenient location according to the older adults' lifestyles. For example, our [focus group study](https://doi.org/10.1186/s12877-021-02252-4) published in the top BMC Geriatrics journal found that some older adults preferred to interact with the speaker in the kitchen while preparing food. Others chose to put the speaker near the bed for a quick conversation before sleeping.

## User-centered design considerations
In addition to the flexible placement, the smart speaker would play a soft prompting ringtone before the frailty conversation, resembling the one used in the airport before any announcements. At the end of the conversation, the speaker would confirm all information was received and appreciate users’ responses. Other design considerations that have not been incorporated into the current system but will be in the future iteration include:
1. adding physical buttons to the smart speaker for those older adults who prefer the familiar, simple button press to the verbal conversation with the smart speaker. The goal was to reduce the complexity or probability of confusion to enhance usability; 
2. adding enjoyable functions to the smart speaker, such as playing music and telling jokes.
