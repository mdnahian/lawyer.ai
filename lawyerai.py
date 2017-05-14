# -*- coding: utf-8 -*-

import json
import requests
from watson_developer_cloud import NaturalLanguageUnderstandingV1
import watson_developer_cloud.natural_language_understanding.features.v1 as \
    features
import nltk
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk_lawyerai import exe_summarizer


deportation = ['deport', 'deportation', 'leave', 'kick']
arrest = ['convict', 'arrest', 'jail']
offenses = ['murder', 'rape', 'sexual', 'drug', 'abuse', 'trafficking', 'racketeer', 'kidnap', 'child', 'treason', 'counterfeit', 'smuggle', 'perjury', 'dui', 'manslaughter', 'license']
overstay = ['overstay', 'violation', 'expire']


visa = ['visa', 'temporary']
type = ['student', 'work', 'marriage']

greencard = ['green', 'card']






def search(text):
    r = requests.get('https://api.cognitive.microsoft.com/bing/v5.0/search?q='+text+'&count=5&offset=0&mkt=en-us&safesearch=Moderate', headers={'Ocp-Apim-Subscription-Key': 'd1d661d02a394b1bab8f052ea2d6a59b'})
    return json.loads(r.text)


def exe_api(text):

    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2017-02-27',
        username='2eded556-1fd1-4c8c-9230-ebcf7acc15c3',
        password='zQ5bnid3hhMZ')

    response = natural_language_understanding.analyze(
        text=text,
        features=[features.Entities(), features.Keywords(), features.Concepts(), features.Sentiment(), features.Emotion()])

    name = ''
    location = ''
    priority = 'LOW'

    for entity in response['entities']:
        if entity['type'] == 'Person':
            name = entity['text']
        elif entity['type'] == 'Location':
            location = entity['text']

    fear = response['emotion']['document']['emotion']['fear']
    anger = response['emotion']['document']['emotion']['anger']

    if fear >= 0.4 or anger >= 0.4:
        priority = 'HIGH'
    elif fear >= 0.3 or anger >= 0.3:
        priority = 'MEDIUM'


    deportation_count = 0
    visa_count = 0
    greencard_count = 0

    words = [w for w in text.split(' ') if not w in stopwords.words("english")]

    base_words = []

    for word in words:
        word = WordNetLemmatizer().lemmatize(word, 'v')
        base_words.append(word)
        if word in deportation:
            deportation_count += 1
        elif word in visa:
            visa_count += 1
        elif word in greencard:
            greencard_count += 1

    stage1 = {'deportation':deportation_count, 'visa':visa_count, 'greencard':greencard_count}
    stage1_ans = max(stage1, key=stage1.get)

    about = '''{
        "concern": "'''+stage1_ans+'''",
    '''

    if stage1_ans == 'deportation':

        for word in base_words:
            if word in arrest:
                # deportation -> arrested -> offense -> information
                offense = ''
                for w in base_words:
                    if w.lower() in offenses:
                        offense = w
                        break
                if offense == '':
                    keywords = [w['text'] for w in response['keywords']]
                    tags = nltk.pos_tag(keywords)
                    for tag in tags:
                        if 'NN' in tag:
                            offense = tag[0]
                            break

                information = ''
                url = '['
                count = 0


                try:
                    results = search('deportation because of '+offense)['webPages']['value']
                    for result in results:
                        url += '''{"link": "'''+result['url']+'''", "name": "'''+result['name']+'''"},'''
                    url = url[:-1]
                    url += ']'

                    while len(information) < 70:
                        u = results[count]['url']
                        information = exe_summarizer(u)
                        count += 1
                except Exception:
                    information = '''
                    Among other things, the person will become ineligible to. receive asylum, as described in Bars to Receiving Asylum or Refugee Status. He or she may also lose eligibility for a U.S. visa or green card, as described. in Crimes. That Make U.S. Visa or Green Card Applicants Inadmissible. If the person is already in the U.S. with a visa or green card, he or she will likely be ordered removed, as described in Crimes. That Will Make an Immigrant Deportable. And if the person somehow gets as far as submitting an application for U.S. citizenship, the aggravated felony conviction will result in not only denial of that application and permanently barred from U.S. citizenship, but in his or her being placed in removal proceedings. There’s a sort of mismatch, in which state crimes that may sound minor to most people, did not involve violence, and may not even be called felonies are nevertheless viewed as aggravated felonies by federal immigration authorities.
                    '''
                    pass

                about += '''
                        "reason": "arrest",
                        "offense": "'''+offense+'''",
                        "information": "'''+information+'''",
                        "url": '''+url+'''
                }
                '''
                break
            elif word in overstay:
                # deported - > overstay -> visa type
                visa_type = ''
                for word in base_words:
                    if word in type:
                        visa_type = word

                about += '''
                        "reason": "overstay",
                        "type": "'''+visa_type+'''"
                }
                '''
                break
    elif stage1_ans == 'visa':

        for word in base_words:
            if word in visa:
                visa_type = ''
                for word in base_words:
                    if word in type:
                        visa_type = word

                information = ''
                url = '['
                count = 0

                try:
                    results = search(' '.join(text.split(' ')[-4:]))['webPages']['value']
                    for result in results:
                        url += '''{"link": "''' + result['url'] + '''", "name": "''' + result['name'] + '''"},'''
                    url = url[:-1]
                    url += ']'

                    while len(information) < 90:
                        u = results[count]['url']
                        information = exe_summarizer(u)
                        count += 1
                except Exception:
                    information = '''
                        There are various types of nonimmigrant visas for temporary visitors to travel to the U.S., if you are not a U.S. citizen or U.S. lawful permanent resident. It's important to have information about the type of nonimmigrant visa you will need for travel, and the steps required to apply for the visa at a U.S. Embassy or Consulate abroad.
                    '''
                    pass

                about += '''
                        "type": "''' + visa_type + '''",
                        "information": "''' + information + '''",
                        "url": ''' + url + '''
                }
                '''
                break

    elif stage1_ans == 'greencard':
        pass
    else:
        about = '''
            {
                "concern": "general"
            }
        '''

    built_json = ''

    try:
        built_json = json.dumps(json.loads('''
            {
                "name": "'''+name.title()+'''",
                "location": "'''+location+'''",
                "priority": "'''+priority+'''",
                "transcript": "'''+text+'''",
                "about": '''+about+'''
            }
        '''), indent=4)

    except Exception:
        print name
        print location
        print priority
        print about

    return built_json




# print str(exe_api('Hello my name is Kevin and I was arrested for dealing drugs I am an immigrant from China so am I think I am in danger of being deported'))
# print str(exe_api('Hi my name is john and am from France and I am in jail right now because of a suspended license please help me'))
# print str(exe_api('hi my name is tim and I am from Cuba and I have a question about extending my student visa'))
# print str(exe_api('hi my name is tim and I am from San Francisco and I have a question about extending my work visa'))
