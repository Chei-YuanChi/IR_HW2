from collections import defaultdict
import re
from django.shortcuts import render
from django import forms
import os
import xml.etree.ElementTree as ET
import json
from nltk import word_tokenize, pos_tag, sent_tokenize
from nltk.corpus import wordnet, stopwords
from nltk.stem import WordNetLemmatizer
from server.models import File_data, Word_index, Word_num, Word_nosw_num, Word_stem_num, IDF, Artical_word_num, Word_Artical, Word_Artical_nosw, Artical_word_num_nosw
from django.core.paginator import Paginator
from math import log
wnl = WordNetLemmatizer()
SW = set(stopwords.words('english'))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spe_ch_list = "~!@#$%^&*()<>+=\{\}\\,./?;:'\"\[\]-_|"
back_space = "@$^*(<+=\{\\/'\"[-_|"
front_space = "~!#%^*)>+=\}\\,./?;'\"\]-_|"

def get_wordnet_pos(tag):
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def stem(sentence):
    lemmas_sent = []
    tagged_sent  = pos_tag(sentence)
    for tag in tagged_sent:
        wordnet_pos = get_wordnet_pos(tag[1]) or wordnet.NOUN
        lemmas_sent.append(wnl.lemmatize(tag[0], pos = wordnet_pos))
    return lemmas_sent

def have_spe(word):
    for x in spe_ch_list:
        if x in word:
            word = word.replace(x, '')
    return word

def replace(user_search, sentence, num_searches):
    new_sentence = ""
    temp_search = user_search
    temp_search = have_spe(temp_search)
    spe_ch = not (user_search == temp_search)
    words = word_tokenize(sentence)
    for i in range(len(words)):
        space = " "
        if words[i] in back_space:
            space = ""
        if i + 1 < len(words):
            if words[i + 1] in front_space:
                space = ""
        else: space = ""
        temp_searches = word_tokenize(temp_search.lower())
        temp_searches = stem(temp_searches)

        temp_search = ""
        for x in temp_searches:
            temp_search += str(x)
        str_find = words[i].lower().find(stem([user_search.lower()])[0])
        temp_words = words[i].lower()
        if spe_ch: temp_words = have_spe(temp_words)
        temp_words = stem([temp_words])

        if (temp_words == stem([temp_search])) and temp_search != '':
            num_searches += 1
            new_sentence += '<span class="bg-warning">' + words[i] + '</span>'  + space
        elif str_find != -1:
            j = 0
            while str_find != -1 :
                num_searches += 1
                str_replace = words[i][str_find : len(stem([user_search])[0]) + str_find]
                new_sentence += words[i][j : str_find] + '<span class="bg-warning">' + str_replace + '</span>'
                j = len(stem([user_search])[0]) + str_find
                str_find = words[i].lower().find(stem([user_search])[0], j)
            new_sentence += words[i][j:] + space
        else:
            new_sentence += words[i] + space
    return new_sentence, num_searches

def simple_replace(stem_search, sentence):
    new_sentence = ""
    words = word_tokenize(sentence)
    for i in range(len(words)):
        space = " "
        if words[i] in back_space:
            space = ""
        if i + 1 < len(words):
            if words[i + 1] in front_space:
                space = ""
        else: space = ""
        stem_word = words[i]
        if have_spe(words[i]) != "":
            temp_word = have_spe(words[i].lower())
            stem_word = stem([temp_word])[0]
        if stem_word == stem_search:
            new_sentence += '<span class="bg-warning">' + words[i] + '</span>'  + space
        else:
            new_sentence += words[i] + space
    return new_sentence

def sw_replace(sentence, num_stopwords):
    new_sentence = ""
    words = word_tokenize(sentence)
    for i in range(len(words)):
        space = " "
        if words[i] in back_space:
            space = ""
        if i + 1 < len(words):
            if words[i + 1] in front_space:
                space = ""
        else: space = ""
        if words[i].lower() not in SW: new_sentence += words[i] + space
        else:
            if words[i + 1] in front_space: new_sentence += words[i] + space
            else: num_stopwords += 1
    return new_sentence, num_stopwords

class FileUploadForm(forms.Form):
    file = forms.FileField(label = "File upload", widget=forms.ClearableFileInput(attrs={'multiple': True}))

def MED(sent_01, sent_02):
    n = len(sent_01)
    m = len(sent_02)

    matrix = [[i + j for j in range(m + 1)] for i in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if sent_01[i - 1] == sent_02[j - 1]: d = 0
            else: d = 1
            matrix[i][j] = min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + d)

    distance_score = matrix[n][m]
   
    return distance_score

def handle_uploaded_file(f):
    save_path = os.path.join(BASE_DIR + '/files', f.name)
    with open(save_path, 'wb+') as fp:
        for chunk in f.chunks():
            fp.write(chunk)

'''def home(request):
    msg = []
    if request.method == 'POST':
        forms = FileUploadForm(request.POST,request.FILES)
        if forms.is_valid():
            files = request.FILES.getlist('file')
            for f in files:
                file_name = str(f)
                if file_name.endswith('.xml') != True and file_name.endswith('.json') != True:
                    msg.append('Format error ( .xml or .json) : ' + file_name)
                else:
                    handle_uploaded_file(f)
                    msg.append('"' + file_name + '"' + ' upload successfully! ')

        else: 
            msg.append('The submitted file is invalid ( empty... ).')
            forms = FileUploadForm()
    else:
        forms = FileUploadForm()

    return render(request,'home.html', locals())'''

def home(request):
    msg = []
    if request.method == 'POST':
        forms = FileUploadForm(request.POST,request.FILES)
        if forms.is_valid():
            num = File_data.objects.all()
            if not num.exists(): title_index = 0
            else: title_index = num.order_by('-Title_index')[0].Title_index + 1
            files = request.FILES.getlist('file')
            for f in files:
                index_list = {}
                file_name = str(f)
                if file_name.endswith('.xml') != True and file_name.endswith('.json') != True and file_name.endswith('.csv') != True:
                    msg.append('Format error ( .xml or .json or .csv) : ' + file_name)
                else:
                    if  file_name.endswith('.xml') or file_name.endswith('.json'):
                        handle_uploaded_file(f)
                    else:
                        import pandas as pd
                        data_set = pd.read_csv(f)
                        df_records = data_set.to_dict('records')
                        if file_name.find('index') != -1:
                            Word_index.objects.bulk_create(Word_index(**vals) for vals in df_records)
                        elif file_name.find('article') != -1:
                            File_data.objects.bulk_create(File_data(**vals) for vals in df_records)
                        #else:
                            #Word_num.objects.bulk_create(Word_num(**vals) for vals in df_records)
                            #Word_nosw_num.objects.bulk_create(Word_nosw_num(**vals) for vals in df_records)
                            #Word_stem_num.objects.bulk_create(Word_stem_num(**vals) for vals in df_records)
                            #IDF.objects.bulk_create(IDF(**vals) for vals in df_records)
                            #Artical_word_num.objects.bulk_create(Artical_word_num(**vals) for vals in df_records)
                            #Artical_word_num_nosw.objects.bulk_create(Artical_word_num_nosw(**vals) for vals in df_records)
                            #Word_Artical.objects.bulk_create(Word_Artical(**vals) for vals in df_records)
                            #Word_Artical_nosw.objects.bulk_create(Word_Artical_nosw(**vals) for vals in df_records)

                    msg.append('"' + file_name + '"' + ' upload successfully! ')
        else: 
            msg.append('The submitted file is invalid ( empty... ).')
            forms = FileUploadForm()
    else:
        forms = FileUploadForm()

    return render(request,'home.html', locals())

def data_extract(f, title_index, index_list):
    import pandas as pd
    df = pd.read_csv(f).drop(['Unnamed: 0'], axis = 1).dropna()
    for title in df['title'].values:
        context = df[df['title'] == title]['abstract'].values[0]
        num_sentences = len(sent_tokenize(context))
        words = word_tokenize(context)
        num_words = num_chars = 0
        for word in words:
            if word not in spe_ch_list:
                num_words += 1
        for i in context: 
            if ord(i) < 127 and ord(i) >= 33: num_chars += 1
        file_data = File_data(Title = title, Context = context, Sentences_num = num_sentences, Words_num = num_words, Chars_num = num_chars, Title_index = title_index)
        file_data.save()
        for i in range(len(words)):
            stem_word =  stem([words[i].lower()])[0]
            if stem_word not in index_list:
                index_list[stem_word] = []
            index_list[stem_word].append([title_index, i])
        title_index += 1
    return title_index, index_list

def search(request):
    search_err = delete_msg = user_search = jsonfile = xmlfile = stem_search = nofile = ""
    total_chars = total_words = total_sentences = total_searches = total_stopwords = 0
    sim_word = []
    set_words = set()
    files = os.listdir(BASE_DIR + '/files')
    if request.method == 'POST':
        if 'ok' in request.POST:
                if 'file_name' not in request.GET:
                    search_err = 'There is no file you can search!'
                else:
                    if request.POST['search'] == '':
                        search_err = 'Your input is empty!'
                    else:
                        user_search = request.POST['search']
        elif 'delete' in request.POST:
            delete_path = os.path.join(BASE_DIR + '/files', str(request.POST['delete']))
            os.remove(delete_path)
            delete_msg = "File is deleted successfully."
            files = os.listdir(BASE_DIR + '/files')
        elif 'revise' in request.POST:
            user_search = request.POST['revise']
    if 'file_name' in request.GET:
        n_sw = False
        xmlfile = jsonfile = ''
        file = request.GET['file_name']
        if len(file.split('~')) > 1:
            n_sw = bool(int(file.split('~')[1]))
        file = file.split('~')[0]
        filepath = os.path.join(BASE_DIR + '/files', str(file))
        if os.path.isfile(filepath) == False:
            nofile = "The request '" + file + "' dowsn't exist."
            return render(request, 'search.html', locals())
        data = []
        if file.endswith('.xml') == True:
            tree = ET.parse('files/' + file)
            root= tree.getroot()
            xmlfile = file
            for titles in root.findall(".//Article"):
                title = titles.find(".//ArticleTitle").text
                text = []
                num_chars = num_words = num_sentences = num_searches = num_stopwords = 0
                for context in titles.findall(".//AbstractText"):
                    texts = context.text
                    sentences = sent_tokenize(texts)
                    label = str(context.get('Label')) 
                    if n_sw:
                        new_sentences = []
                        for sentence in sentences:
                            new_sentence, num_stopwords = sw_replace(sentence, num_stopwords)
                            new_sentences.append(new_sentence)
                            for i in new_sentence:
                                if ord(i) < 127 and ord(i) >= 33: num_chars += 1
                            words = word_tokenize(new_sentence)
                            for word in words:
                                if word not in spe_ch_list:
                                    num_words += 1
                                    set_words.add(stem([word.lower()])[0])
                        sentences = new_sentences
                        if label != "":
                            label, num_stopwords = sw_replace(label, num_stopwords)
                    else: 
                        for i in texts:
                            if ord(i) < 127 and ord(i) >= 33: num_chars += 1
                        words = word_tokenize(texts) 
                        for word in words:
                            if word not in spe_ch_list:
                                num_words += 1
                                set_words.add(stem([word.lower()])[0])
                    num_sentences += len(sentences)
                    new_sentences = []
                    set_words.add(stem([label.lower()])[0])
                    if user_search == "":
                        if label != 'None': text += [['[' + label + ']', sentences]]
                        else: text += [['', sentences]]
                    else:
                        for sentence in sentences:
                            new_sentence, num_searches = replace(user_search, sentence, num_searches)
                            new_sentences.append(new_sentence)
                        if label != "None":
                            new_label, num_searches = replace(user_search, label, num_searches)
                            text += [['[' + new_label + ']', new_sentences]]
                        else:
                            text += [['', new_sentences]]
                total_chars += num_chars
                total_words += num_words
                total_sentences += num_sentences
                if n_sw: new_title, _ = sw_replace(title, num_stopwords)
                else: new_title = title
                words = word_tokenize(new_title.lower())
                for x in stem(words): set_words.add(x)
                if user_search != "":
                    new_title, num_searches = replace(user_search, new_title, num_searches)
                    total_searches += num_searches
                data += [[new_title, text, num_chars, num_words, num_sentences, num_searches, num_stopwords]]
                total_stopwords += num_stopwords
        elif file.endswith('json') == True:
            jsonfile = file
            with open(os.path.join('files/', file), encoding="utf-8") as json_file:
                datas = json.load(json_file)
                for user in datas:
                    user_name = user['username']
                    set_words.add(user_name)
                    num_chars = num_words = num_sentences = num_searches = num_stopwords = 0
                    texts = user['tweet_text']
                    sentences = sent_tokenize(texts)
                    num_sentences += len(sentences)
                    total_sentences += len(sentences)
                    sentences = texts.split('\n')
                    if n_sw:
                        new_sentences = []
                        for sentence in sentences:
                            new_sentence, num_stopwords = sw_replace(sentence, num_stopwords)
                            new_sentences.append(new_sentence)
                            for i in new_sentence:
                                if ord(i) < 127 and ord(i) >= 33: num_chars += 1
                            words = word_tokenize(new_sentence)
                            for word in words:
                                if word not in spe_ch_list:
                                    num_words += 1
                                    set_words.add(stem([word.lower()])[0])
                        sentences = new_sentences
                    else: 
                        for i in texts:
                            if ord(i) < 127 and ord(i) >= 33: num_chars += 1
                        words = word_tokenize(texts) 
                        for word in words:
                            if word not in spe_ch_list:
                                num_words += 1
                                set_words.add(stem([word.lower()])[0])
                    total_chars += num_chars
                    total_words += num_words
                    if user_search == "":
                        data += [[user_name, sentences, num_chars, num_words, num_sentences, num_searches, num_stopwords]]
                    else:
                        new_sentences = []
                        for sentence in sentences:
                            new_sentence, num_searches = replace(user_search, sentence, num_searches)
                            new_sentences.append(new_sentence)
                        new_username, num_searches = replace(user_search, user_name, num_searches)
                        total_searches += num_searches
                        data += [[new_username, new_sentences, num_chars, num_words, num_sentences, num_searches, num_stopwords]] 
                    total_stopwords += num_stopwords
        if user_search != "" and total_searches == 0:
            dict_word = {}
            for word in set_words:
                dict_word[word] = MED(word, user_search)
            sim_word = sorted(dict_word.items(), key=lambda d: d[1])[0:5]
            sim_word = [i for i, j in sim_word]
            search_err = 'No results for "'+ user_search + '". Do you want to search ' 
        temp_searches = have_spe(user_search)
        if temp_searches != '':
            temp_searches = word_tokenize(temp_searches.lower())
            temp_searches = stem(temp_searches)
            stem_search = ""
            for x in temp_searches:
                stem_search += str(x)  
        else : stem_search = user_search
    return render(request, 'search.html', locals())

def draw_graph(x, y, name):
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9,9))
    plt.bar(range(len(x)), y, 0.5, color = 'blue', alpha = .5)
    '''plt.xticks(range(len(x)), x)
    plt.xticks(rotation = 'vertical')
    plt.xticks(fontsize = 8)'''
    plt.xlabel('Number of words')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(BASE_DIR + '/server/static', name))
    plt.close()
    return name

def draw_line_graph(x, y, name):
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12,12))
    plt.plot(x, y, color = 'blue')
    plt.xlabel('words')
    plt.xticks(rotation = 'vertical')
    plt.ylabel('tf-idf')
    plt.savefig(os.path.join(BASE_DIR + '/server/static', name))
    plt.close()
    return name

def sort_dic(words):
    sorted_word = sorted(words.items(), key=lambda d: d[1], reverse=True)
    words = [i for i, j in sorted_word]
    counts = [j for i, j in sorted_word]
    return words, counts, words[0], counts[0], words[len(words) - 1] ,counts[len(counts) - 1]


def multiple_search(request):
    show = gogo = 0
    show_page = 1
    search_err = user_search = file = ""
    if 'page' in request.GET:
        if request.GET.get('page').find('~') != -1:
            user_search = request.GET['page'].split('~')[1]
            if user_search != '': gogo = 1
    if request.method == 'POST' or gogo:
        if 'search' in request.POST:
            if request.POST['search'] == '':
                search_err = 'Your input is empty!'
                return render(request, 'multiple_search.html', locals())
        if 'revise' in request.POST: user_search = request.POST['revise']
        elif 'search' in request.POST: user_search = request.POST['search']
        set_words = set()
        stem_search = user_search
        if user_search not in spe_ch_list:
            temp_searches = stem(word_tokenize(have_spe(user_search).lower()))
            stem_search = ""
            for x in temp_searches:
                stem_search += str(x)
        search_index = Word_index.objects.filter(Word = stem_search)
        if not search_index.exists():
            total_searches = 0
            dict_word = {}
            datas =  Word_index.objects.all()
            for data in datas: set_words.add(data.Word)
            for word in set_words:
                dict_word[word] = MED(word, stem_search)
            sim_word = sorted(dict_word.items(), key=lambda d: d[1])[0:5]  
            sim_word = [i for i, j in sim_word]
            search_err = 'No results for "'+ user_search + '". Do you want to search ' 
            show_page = 0
            return render(request, 'multiple_search.html', locals())
        total_search = {}
        datas = search_index[0]
        total_searches = len(datas.Index)
        for data in datas.Index:
            count = total_search.get(data[0], 0)
            total_search[data[0]] = count + 1
        total_articles = len(total_search)
        index, num_searches, _, _, _, _ = sort_dic(total_search)
        data_list = []
        page = Paginator(index, 20)
        if request.GET.get('page').find('~') != -1:
            page_number = request.GET.get('page').split('~')[0]
        else: page_number = request.GET.get('page')
        page_obj = page.get_page(page_number)
        if int(page_obj.paginator.num_pages) == 20:
            index = index[(int(page_number) - 1) * 20 :]
        else:
            index = index[(int(page_number) - 1) * 20 : int(page_number) * 20]
        for i in index:
            get_file = File_data.objects.filter(Title_index = i)
            title = get_file[0].Title
            context = get_file[0].Context
            contexts = sent_tokenize(context)
            num_sentences = get_file[0].Sentences_num
            num_words = get_file[0].Words_num
            num_chars = get_file[0].Chars_num
            title = simple_replace(stem_search, title)
            context = simple_replace(stem_search, contexts[0])
            data_list.append([title, i, num_sentences, num_words, num_chars, total_search[i], context])

        return render(request, 'multiple_search.html', locals())
    else:
        datas =  Word_index.objects.all()
        if not datas.exists():
            search_err = 'There is no data you can search.'
            return render(request, 'multiple_search.html', locals())
        data_list = []
        total_searches = 0
        get_files = File_data.objects.all()
        total_articles = get_files.count()
        if 'page' in request.GET:
            if request.GET.get('page').find('~') != -1:
                page_number = request.GET.get('page').split('~')[0]
            else: page_number = request.GET.get('page')
            page = Paginator(get_files, 20)
            page_obj = page.get_page(page_number)
            if int(page_obj.paginator.num_pages) == 20:
                get_files = get_files[(int(page_number) - 1) * 20 :]
            else:
                get_files = get_files[(int(page_number) - 1) * 20 : int(page_number) * 20]
            for get_file in get_files:
                index =  get_file.Title_index
                title = get_file.Title
                context = get_file.Context
                contexts = sent_tokenize(context)
                num_sentences = get_file.Sentences_num
                num_words = get_file.Words_num
                num_chars = get_file.Chars_num
                data_list.append([title, index, num_sentences, num_words, num_chars, total_searches, contexts[0]])
        elif 'statistic' in request.GET:
            show = 1
            total_words = total_words_nosw = total_words_stem = 0
            total_words_name = 'words.png'
            total_nosw_words_name = 'words_nosw.png'
            total_stem_words_name = 'words_stem.png'
            words, counts = get_data(Word_num.objects.all())
            for i in range(len(words)):
                total_words += counts[i]
            draw_graph(words[:50], counts[:50], 'words.png')
            data_word = []
            for i in range(5):
                data_word.append([i + 1, words[i], counts[i], round(counts[i] / total_words, 3)])
            words, counts = get_data(Word_nosw_num.objects.all())
            for i in range(len(words)):
                total_words_nosw += counts[i]
            draw_graph(words[:50], counts[:50], 'words_nosw.png')
            data_word_nosw = []
            for i in range(5):
                data_word_nosw.append([i + 1, words[i], counts[i], round(counts[i] / total_words_nosw, 3)])
            words, counts = get_data(Word_stem_num.objects.all())
            for i in range(len(words)):
                total_words_stem += counts[i]
            draw_graph(words[:50], counts[:50], 'words_stem.png')
            data_word_stem = []
            for i in range(5):
                data_word_stem.append([i + 1, words[i], counts[i], round(counts[i] / total_words_stem, 3)])

    return render(request, 'multiple_search.html', locals())

def get_data(word_list):
    words = []
    counts = []
    for data in word_list:
        words.append(data.Word)
        counts.append(int(data.Counts))
    return words, counts


def search_database(request):
    n_sw = False
    show = 0
    nofile = user_search = search_err = ''
    total_chars = total_words = total_sentences = total_searches = total_stopwords = 0
    if 'index' in request.GET:
        index = request.GET['index']
        if len(index.split('~')) > 1:
            n_sw = bool(int(index.split('~')[1]))
        index = int(index.split('~')[0])
        if not File_data.objects.filter(Title_index = index).exists():
            nofile = 'Your search doesn\'t exsit.'
        get_file =  File_data.objects.filter(Title_index = index)
        title = get_file[0].Title
        context = get_file[0].Context
        total_sentences = get_file[0].Sentences_num
        total_words = get_file[0].Words_num
        total_chars = get_file[0].Chars_num
        sentences = sent_tokenize(context)
        if n_sw:
            words = word_tokenize(context)
            new_sentence = ''
            for i in range(len(words)):
                if words[i].lower() in SW:
                    total_stopwords += 1
                else:
                    space = " "
                    if words[i] in back_space:
                        space = ""
                    if i + 1 < len(words):
                        if words[i + 1] in front_space:
                            space = ""
                    else: 
                        space = ""
                    new_sentence += words[i] + space
            sentences = sent_tokenize(new_sentence)

    if request.method == 'POST':
        if 'search' in request.POST:
            if request.POST['search'] == '':
                search_err = 'Your input is empty!'
                return render(request, 'search_database.html', locals())
        if 'revise' in request.POST:  user_search = request.POST['revise']
        else: user_search = request.POST['search']
        if 'Statistic' in request.GET:
            index = request.GET['Statistic']
        stem_search = user_search
        if user_search not in spe_ch_list:
            temp_search = have_spe(user_search)
            temp_searches = word_tokenize(temp_search.lower())
            temp_searches = stem(temp_searches)
            stem_search = ""
            for x in temp_searches:
                stem_search += str(x)
        search = Word_index.objects.filter(Word = stem_search)
        words_index = []
        if search.exists():
            for search_index in search[0].Index:
                if search_index[0] == index:
                    words_index.append(search_index[1])
        if len(words_index) == 0 or (n_sw and stem_search in SW):
            set_words = set()
            dict_word = {}
            datas =  Word_index.objects.all()
            for data in datas: 
                for data_index in data.Index:
                    if data_index[0] == index:
                        if (n_sw and data.Word not in SW) or n_sw != True:
                            set_words.add(data.Word)
                            break
            for word in set_words:
                dict_word[word] = MED(word, stem_search)
            sim_word = sorted(dict_word.items(), key=lambda d: d[1])[0:5]  
            sim_word = [i for i, j in sim_word]
            search_err = 'No results for "'+ user_search + '". Do you want to search ' 
            return render(request, 'search_database.html', locals())
        total_searches = len(words_index)
        words = word_tokenize(context)
        new_sentence = ''
        for i in words_index:
            words[i] = '<span class="bg-warning">' + words[i] + '</span>'
        for i in range(len(words)):
            if n_sw and words[i].lower() in SW:
                total_stopwords += 1
            else:
                space = " "
                if words[i] in back_space:
                    space = ""
                if i + 1 < len(words):
                    if words[i + 1] in front_space:
                        space = ""
                else: space = ""
                new_sentence += words[i] + space
        sentences = sent_tokenize(new_sentence)
    elif 'Statistic' in request.GET:
        show = 1
        index = request.GET['Statistic']
        artical_words_num = Artical_word_num.objects.filter(Artical_index  = int(index))[0]
        datas = Word_Artical.objects.filter(Artical_index  = int(index))
        tf_idf = {}
        for data in datas:
            word = data.Word
            count = data.Counts
            idf = IDF.objects.filter(Word = word)[0]
            tf_idf[word] = (count / artical_words_num.Counts) * log(len(Artical_word_num.objects.all()) / idf.Artical_num)
        
        word, tfidf, _, _, _, _ = sort_dic(tf_idf)
        name = draw_line_graph(word[:25], tfidf[:25], 'index_' + str(index) + '.png')
        top = []
        for i in range(5):
            top.append([i + 1, word[i], round(tfidf[i], 3)])

        artical_words_num_nosw = Artical_word_num_nosw.objects.filter(Artical_index  = int(index))[0]
        datas_nosw = Word_Artical_nosw.objects.filter(Artical_index  = int(index))
        tf_idf_nosw = {}
        for data in datas_nosw:
            word = data.Word
            count = data.Counts
            idf = IDF.objects.filter(Word = word)[0]
            tf_idf_nosw[word] = (count / artical_words_num_nosw.Counts) * log(len(Artical_word_num_nosw.objects.all()) / idf.Artical_num)
        
        word_nosw, tfidf_nosw, _, _, _, _ = sort_dic(tf_idf_nosw)
        name_nosw = draw_line_graph(word_nosw[:25], tfidf_nosw[:25], 'index_' + str(index) + '(nosw).png')
        top_nosw = []
        for i in range(5):
            top_nosw.append([i + 1, word_nosw[i], round(tfidf_nosw[i], 3)])
    return render(request, 'search_database.html', locals())