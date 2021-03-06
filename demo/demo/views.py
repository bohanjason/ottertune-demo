from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.generic.list import ListView
from django.utils import timezone
from django.core.mail import send_mail

from .forms import SignUpForm
from .models import KnobCatalog, Config
from django.views.decorators.csrf import csrf_exempt
from django.template.context_processors import csrf
from django.http import HttpResponse
import json
import logging
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ..settings import EMAIL_FROMADDR, EMAIL_PWD
from django.core.exceptions import ObjectDoesNotExist


# Logging
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


ip = 'http://192.168.2.183:8000'
upload_code = 'XB0P94PTIOKS1ZZPC9QW'

@login_required
def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            # benchmark = form.get('benchmark')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('tpcc')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

@csrf_exempt
def tpcc(request):

    if request.method == 'POST':
        knobs_setting = {}
        post = request.POST
        for k in post:
            if k != "username" and k != "email":
                print (k)
                knobs_setting[k] = post[k]
        config = Config.objects.create(username = post["username"],
                                      email = post["email"],
                                      knobs_setting = json.dumps(knobs_setting))
        config.save()
        config_id = config.pk
        print (config_id)
        print (knobs_setting)

    knobs = KnobCatalog.objects.all()
    settings = []
    for knob in knobs:
        settings.append((knob, [k.strip() for k in knob.setting.split(",")]))
    
    return render(request, 'select.html', {"knobs": settings, "nbar": "tune"})


@csrf_exempt
def tasks(request):
    tasks = Config.objects.all()
    return render(request, 'task.html', {'tasks': tasks, "nbar": "tasks"})

def get_result(request, task_id):
    try:
        config = Config.objects.get(pk=task_id)
        if(config.status == 'FINISHED'):
            return HttpResponse("FINISHED BEFORE")
        config.status = 'RUNNING'
        config.save()
    except Config.DoesNotExist:
        LOG.warning("Invalid task id: %s", task_id)
        return HttpResponse("Invalid task id: " + task_id)

    print ("get result id {}".format(task_id))
    return HttpResponse(config.knobs_setting)

def lead(request):

    url = ip + '/get_max_throughput/' + upload_code
    response = json.loads(urllib.request.urlopen(url).read().decode())
    best_id = response['id'] 
    best_perf = round(response['throughput'], 2)
    best_knobs = response['knobs']

    if (best_id > 0):
        try:
            ot = Config.objects.get(username = 'OtterTune')
            ot.throughput = best_perf
            ot.knobs_setting = best_knobs
            ot.email = best_id # result id on the ottertune server
        except ObjectDoesNotExist:
            ot = Config.objects.create(username = 'OtterTune',
                                       email = best_id,
                                       knobs_setting = best_knobs, 
                                       throughput = best_perf,
                                       status = 'FINISHED')
        ot.save()

    leads = Config.objects.filter(status='FINISHED').order_by('-throughput')
    return render(request, 'lead.html', {'leads': leads, "nbar": "lead"})

def biglead(request):
   # ip = 'http://192.168.2.21:8000'
   # upload_code = 'XB0P94PTIOKS1ZZPC9QW'
    url = ip + '/get_max_throughput/' + upload_code
    response = json.loads(urllib.request.urlopen(url).read().decode())
    best_id = response['id'] 
    best_perf = round(response['throughput'], 2)
    best_knobs = response['knobs']

    if (best_id > 0):
        try:
            ot = Config.objects.get(username = 'OtterTune')
            ot.throughput = best_perf
            ot.knobs_setting = best_knobs
        except ObjectDoesNotExist:
            ot = Config.objects.create(username = 'OtterTune',
                                       email = 'ottertune@cs.cmu.edu',
                                       knobs_setting = best_knobs, 
                                       throughput = best_perf,
                                       status = 'FINISHED')
        ot.save()

    leads = Config.objects.filter(status='FINISHED').order_by('-throughput')
    return render(request, 'biglead.html', {'leads': leads, "nbar": "lead"})

def task_info(request, task_id):
    knobs = KnobCatalog.objects.all()
    settings = []

    try:
        config = Config.objects.get(pk=task_id)
        if(int(task_id) == 1): # default
            knobs_setting = {'default_statistics_target': '100', 'checkpoint_timeout': '5min', 'effective_cache_size': '128MB', 'effective_io_concurrency': '1', 'commit_siblings': '5', 'wal_buffers': '4MB', 'checkpoint_segments': '3', 'shared_buffers': '128MB', 'bgwriter_lru_maxpages': '100', 'commit_delay': '0'}    
        else:
            knobs_setting = json.loads(config.knobs_setting)
        for knob in knobs:
            if knob.name in knobs_setting:
                settings.append((knob, knobs_setting[knob.name]))
            else:
                settings.append((knob, knobs_setting["global." + knob.name]))
    except Config.DoesNotExist:
        LOG.warning("Invalid task id: %s", task_id)
        return HttpResponse("Invalid task id: " + task_id)
    return render(request, 'info.html', {'task': config, "settings": settings})

def send_email(toAddr, subject, body):
    try:  
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # Authentication
        server.login(EMAIL_FROMADDR, EMAIL_PWD)

        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROMADDR
        msg['To'] = toAddr
        msg['Subject'] = subject
        #body = "your task throughput: 999, rank: 1"
        msg.attach(MIMEText(body, 'plain'))

        # Converts the Multipart msg into a string
        text = msg.as_string()
        # sending the mail
        server.sendmail(EMAIL_FROMADDR, toAddr, text)
        # terminating the session
        server.quit()
    except:  
        print ('Something went wrong when sending emails...')

@csrf_exempt
def new_result(request):
    if request.method == 'POST':
        throughput = round(float(request.POST['throughput']), 2)
        task_id = request.POST['task_id']
        print (throughput)
        print (task_id)
        try:
            config = Config.objects.get(pk=task_id)
            config.throughput = throughput
            config.status = 'FINISHED'
            config.save()
            #send_email(config.email, "OtterTune Demo Result",
            #          "your task throughput: 999, rank: 1")
        except Config.DoesNotExist:
            LOG.warning("Invalid task id: %s", task_id)
        return HttpResponse("task id: {}, throughput (txn/sec): {}".format(task_id, throughput))
    LOG.warning("Request type was not POST")
    return HttpResponse("Request type was not POST")
