import pyaudio, json, random, pyttsx3, morfeusz2, string, threading
from vosk import Model, KaldiRecognizer, SetLogLevel
from datetime import datetime, timedelta
from termcolor import colored
from typing import Literal

morf = morfeusz2.Morfeusz()
last_awake = datetime.now()
awake_delay = 30 #seconds
debug = True

algorytm = json.load(open('data.json',encoding='utf-8'))


def debug_log(msg: str, level: Literal[1, 2, 3]) -> None:
    if debug == True:
        level_colors = {1: 'green', 2: 'yellow', 3: 'red'}
        print(colored(msg, level_colors[level]))

def init_func(task):
    match task:
        case 'przywitanie': #func_call
            speak('test')
        case 'godzina': #func_call
            speak('test')
        case 'pogoda_dzis': #func_call
            speak('test')
        case 'pogoda_jutro': #func_call
            speak('test')
        case 'pogoda_pojutrze': #func_call
            speak('test')

def analyse_(sentence) -> dict:
    accuracy = {'accuracy':[0,0], 'lemmat':[]}
    sentence = sentence.translate(str.maketrans('', '', string.punctuation)).split(' ')
    try:
        for word in sentence:
            analyse = morf.analyse(str(word))
            if not analyse: #nie znaleziono slowa
                print(word)
                accuracy['accuracy'][1] += 1
                accuracy['lemmat'].append('')
            else:
                pewnosc_temp = (1/len(analyse))*100
                bazowa_forma = analyse[0][2][1]
                print(f"Word: {word}    Lemmat: {bazowa_forma}    Accuracy: {pewnosc_temp}%")
                accuracy['accuracy'][0] += pewnosc_temp
                accuracy['accuracy'][1] += 1
                if ':' in bazowa_forma: accuracy['lemmat'][word] = bazowa_forma.split(':')[0]
                else: accuracy['lemmat'].append(bazowa_forma)
    except Exception as e:
        pass #
    return {'status':True, 'accuracy':"{:.2f}%".format(accuracy['accuracy'][0]/accuracy['accuracy'][1]), 'data':accuracy}

# SEKCJA GLOSOWA
def speak(text):
    robot = pyttsx3.init()
    robot.setProperty('rate', 140)
    #robot.isBusy()
    robot.say(text)
    if robot.isBusy():
        robot.runAndWait()

# SEKCJA ALGORYTMU
def extract_keyword(text, data):
    temp_data = []
    collected_data = {'status':'found', 'detected_mode':'null', 'keyword_found':[], 'extended_found':[], 'response':False}
    
    #SEKCJA KEYWORD
    if data['multiple_keyword'] == True and data['declination_keyword'] == False:
        found_data = [word for word in text if word in data['keyword']]
        if len(found_data) <= 1:
            return {'status':'not found', 'detected_mode':'keyword: true/false'}
        collected_data['keyword_found'] = found_data
    elif data['multiple_keyword'] == True and data['declination_keyword'] == True:
        for word in data['keyword']:
            for t in text:
                if t.startswith(word) == True:
                    temp_data.append(t)
                else:
                    return {'status':'not found', 'detected_mode':'keyword: true/true'}
        else:
            collected_data['keyword_found'] = temp_data
            collected_data['detected_mode'] = 'keyword: true/true'
    elif data['multiple_keyword'] == False and data['declination_keyword'] == False:
        found_data = [word for word in text if word in data['keyword']]
        if len(found_data) == 0 or len(found_data) > 1:
            return {'status':'not found', 'detected_mode':'keyword: false/false'}
        collected_data['keyword_found'] = found_data
        collected_data['detected_mode'] = 'keyword: false/false'
    elif data['multiple_keyword'] == False and data['declination_keyword'] == True:
        for word in data['keyword']:
            for t in text:
                if t.startswith(word) == True:
                    temp_data.append(t)
            else:
                if len(temp_data) != 1:
                    return {'status':'not found', 'detected_mode':'keyword: false/true'}
        collected_data['keyword_found'] = temp_data
        collected_data['detected_mode'] = 'keyword: false/true'

    if data['extended'] != False:

        #SEKCJA EXTENDED
        if data['multiple_extended'] == True and data['declination_extended'] == False:
            found_data = [word for word in text if word in data['extended']]
            if len(found_data) != len(data['extended']): return {'status':'not found', 'detected_mode':'extended: true/false'}
            collected_data['extended_found'] = found_data
            collected_data['detected_mode'] = 'extended: true/false'
        elif data['multiple_extended'] == True and data['declination_extended'] == True:
            for word in data['extended']:
                for t in text:
                    if t.startswith(word) == False:
                        return {'status':'not found', 'detected_mode':'extended: true/true'}
                    else:
                        temp_data.append(t)
            collected_data['extended_found'] = temp_data
            collected_data['detected_mode'] = 'extended: true/true'
        elif data['multiple_extended'] == False and data['declination_extended'] == False:
            found_data = [word for word in text if word in data['extended']]
            if len(found_data) < 1: return {'status':'not found', 'detected_mode':'extended: false/false'}
            collected_data['extended_found'] = found_data
            collected_data['detected_mode'] = 'extended: false/false'
        elif data['multiple_extended'] == False and data['declination_extended'] == True:
            for word in data['extended']:
                for t in text:
                    if t.startswith(word) == True:
                        temp_data.append(t)
            if len(temp_data) == 0:
                return {'status':'not found', 'detected_mode':'extended: false/true'}
            collected_data['extended_found'] = temp_data
            collected_data['detected_mode'] = 'extended: false/true'
    
    #SEKCJA RESPONSE
    if data['response'] != False: collected_data['response'] = data['response']
    
    return collected_data

def init_activity(raw_text):
    global last_awake
    match = []

    print(analyse_(raw_text))
    
    words = raw_text.split(' ')
    elapsed_time = datetime.now() - timedelta(seconds=awake_delay)
    if elapsed_time < last_awake or words[0] == 'test': # <- awake word 'test'
        if words[0] == 'test':
            last_awake = datetime.now()
        for x in algorytm['algo']:
            #if len(match) > 0: break
            resp = extract_keyword(words, algorytm['algo'][x]['keywords'])
            if resp['status'] == 'found':
                match.append(x)
        else:
            if len(match) == 0: return "not found"
            elif len(match) > 1: return "too many"
            elif len(match) == 1:
                print(match)
                return match[0]
    return 'last_awake'


def chat_test():
    while True:
        text = input(' > ')
        if text == 'quit': break
        res = init_activity(text)
        debug_log(f' > [{res}] {random.choice(algorytm["algo"][res]["keywords"]["response"])}', 1)

def mic_test():
    SetLogLevel(-1)
    model = Model(model_path=f"model", lang="pl-PL")
    recognizer = KaldiRecognizer(model, 16000)
    mic = pyaudio.PyAudio()
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    while True:
        stream.start_stream()
        data = stream.read(4096)
        if recognizer.AcceptWaveform(data):
            text = recognizer.Result()
            if text[14:-3] != '':
                res = init_activity(text[14:-3])
                debug_log(f' > [{res}] {random.choice(algorytm["algo"][res]["keywords"]["response"])}', 1)

if __name__ == "__main__":
    chat_test()
    #mic_test()