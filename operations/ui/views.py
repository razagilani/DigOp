from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render_to_response
from ui.models import LoginForm
from ui.models import BookForm
from ui.models import ProcessingForm
from ui.models import Book
from ui.models import ProcessingSession
from django.contrib.auth.models import User, UserManager
import urllib, urllib2
import sys
import suds
from optparse import OptionParser
from pprint import pprint
from datetime import datetime
from dateutil.parser import parse
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.template import Library
from datetime import timedelta
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Avg
from django.template import Library, Node
from django.contrib.messages import constants as messages
from django.contrib import messages

#django-qsstats-magic Should be install before running the app
#python-dateutil

import time
use = None
register = Library()

def login(request):
    def errorHandle(error):
        form = LoginForm()
        return render_to_response('login.html', {
            'error' : error,
            'form' : form,
        })
    if request.method == 'POST': # If the form has been submitted...
        form = LoginForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            username = request.POST['username']
            password = request.POST['password']
            use = authenticate(username=username, password=password)
            request.session['user_id'] = use
            if use is not None:
                auth_login(request, use)
                return HttpResponseRedirect('/index/')
            else: # Return a 'disabled account' error message
                error = 'account disabled'
                return errorHandle(error)

        else:
            error = 'form is invalid'
            return errorHandle(error)
    else:
        form = LoginForm() # An unbound form
        return render_to_response('login.html', {
            'form': form,
        })

@login_required
def indexPage(request):
    form = BookForm()
    if request.user.is_superuser == True:
        return render_to_response('admin_page.html', {
        },context_instance=RequestContext(request))
    else:
        return render_to_response('logged_in.html', {
                        'form' : form,
        },context_instance=RequestContext(request))

def adminSessionData(request):
    form = BookForm()
    return render_to_response('admin_session.html', {
                        'form' : form,
            },context_instance=RequestContext(request))

def showUsers(request):
    return render_to_response('admin_login.html', {
            'users':User.objects.all(),
            },context_instance=RequestContext(request))

def barcodePage(request):
	return render_to_response('getbarcode.html', {

            },context_instance=RequestContext(request))

def barcodeReport(request):
	if request.method == 'POST': # If the form has been submitted...
		bar = request.POST['barcode']
		dict = None
		list = []
		try:
			book = Book.objects.get(barcode=bar)
		except Book.DoesNotExist:
			messages.add_message(request, messages.ERROR, 'Barcode does not exist ')
			return render_to_response('barcoderesult.html', {
				'list' : list,
			},context_instance=RequestContext(request))
		result = ProcessingSession.objects.filter(book=book)
		for item in result:
			fmt = '%Y-%m-%d %H:%M:%S'
			d1 = datetime.strptime(str(item.endTime),fmt)
			d2 = datetime.strptime(str(item.startTime),fmt)
			d1_ts = time.mktime(d1.timetuple())
			d2_ts = time.mktime(d2.timetuple())
			dict = {'barcode':item.book.barcode, 'duration':str(item.endTime - item.startTime), 'objects':item.pagesDone, 'user':item.user, 'isFinished':item.operationComplete,'rate':int(int(item.pagesDone)/(float(d1_ts-d2_ts)/(60*60))),'task':item.task,'startTime':item.startTime}
			list.append(dict)
		messages.add_message(request, messages.SUCCESS, 'Results of Barcode '+ bar + ' are as follows: ')
		return render_to_response('barcoderesult.html', {
				'list' : list,
        },context_instance=RequestContext(request))


def reportMenu(request):
    return render_to_response('reportmenu.html', {

            },context_instance=RequestContext(request))

def processBookForm(request):
    use=request.user
    def errorHandle(error):
        form = BookForm()
        return render_to_response('logged_in.html', {
            'error' : error,
            'form' : form,
        })
    if request.method == 'POST': # If the form has been submitted...
        book = None
        form = BookForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            bar = request.POST['barcode']
            try:
                book = Book.objects.get(barcode=bar)
            except Book.DoesNotExist:
                book = None
            if book is None:
                url='http://128.164.212.164:8080/BarcodeService/WSBarcodePages?wsdl'
                client = suds.client.Client(url)
                pages = client.service.getPages(bar)
                book = Book.objects.create(barcode=bar, totalPages=pages)
                book.save()
                messages.add_message(request, messages.SUCCESS, 'Book object with barcode '+ bar + ' created successfully')
                return render_to_response('processingForm.html', {
                        'form' : ProcessingForm(initial={'book': book,
                                                        'user':request.user,}),
						},context_instance=RequestContext(request))
            else:
				messages.add_message(request, messages.ERROR, 'Book object with barcode '+ bar + ' exists')
				return render_to_response('processingForm.html', {
                        'form' : ProcessingForm(initial={'book': book,
                                                        'user':request.user,}),
						},context_instance=RequestContext(request))
        else:
            error = 'form is invalid'
            return errorHandle(error)
    else:
        form = BookForm() # An unbound form
        return render_to_response('logged_in.html', {
            'form': form,
        },context_instance=RequestContext(request))

def processProcessingForm(request):
    use=request.user
    def errorHandle(error):
        form = ProcessingForm()
        return render_to_response('logged_in.html', {
            'error' : error,
            'form' : form,
        })
    if request.method == 'POST': # If the form has been submitted...
        form = ProcessingForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            bookid = request.POST['book']
            bookObject = Book.objects.get(id = bookid)
            pages = request.POST['pagesDone']
            comm = request.POST['comments']
            complete = request.POST['operationComplete']
            openingDate = request.POST['startTime']
            closingDate = request.POST['endTime']
            tasktype = request.POST['task']
            bst = None
            bst = ProcessingSession(book=Book.objects.get(id =request.POST['book']),user=User.objects.get(id=request.POST['user']),pagesDone=pages,comments=comm,operationComplete=complete,startTime=openingDate,endTime=closingDate,task=tasktype)
            bst.save()
            messages.add_message(request, messages.SUCCESS, 'record added successfully')
            return render_to_response('pages.html', {
                 },context_instance=RequestContext(request)
                 )


        else:
            error = 'form is invalid'
            return errorHandle(error)
    else:
        form = ProcessingForm() # An unbound form
        return render_to_response('logged_in.html', {
            'form': form,
        },context_instance=RequestContext(request))


def produceData(request):
    name = request.GET.get('user')
    start = request.GET.get('start')
    end = request.GET.get('end')
    myList = []
    if name != 'all':
        a = ProcessingSession.objects.filter(user__username=name).filter(startTime__gte = start)
        c = ProcessingSession.objects.filter(user__username=name).filter(startTime__lte = end)
        b = a & c
        dict = None

        for item in b:
            fmt = '%Y-%m-%d %H:%M:%S'
            d1 = datetime.strptime(str(item.endTime),fmt)
            d2 = datetime.strptime(str(item.startTime),fmt)
            d1_ts = time.mktime(d1.timetuple())
            d2_ts = time.mktime(d2.timetuple())
            if item.endTime is not None:
				dict = {'barcode':item.book.barcode, 'duration':str(item.endTime - item.startTime), 'objects':item.pagesDone, 'user':name, 'isFinished':item.operationComplete,'rate':int(int(item.pagesDone)/(float(d1_ts-d2_ts)/(60*60))),'task':item.task,'startTime':item.startTime }
            else:
				dict = {'barcode':item.book.barcode, 'duration':None, 'objects':item.pagesDone, 'user':name, 'isFinished':item.operationComplete,'rate':int(int(item.pagesDone)/(float(d1_ts-d2_ts)/(60*60))),'task':item.task,'startTime':item.startTime }
            myList.append(dict)
    else:
        b = ProcessingSession.objects.all();
        dict = None
        for item in b:
            us = item.user.username
            fmt = '%Y-%m-%d %H:%M:%S'
            d1 = datetime.strptime(str(item.endTime),fmt)
            d2 = datetime.strptime(str(item.startTime),fmt)
            d1_ts = time.mktime(d1.timetuple())
            d2_ts = time.mktime(d2.timetuple())
            if item.endTime is not None:
				if item.task == 'Scan':
					obj = OperationScan.objects.get(book = item.book)
				elif item.task == 'QC':
					obj = OperationQc.objects.get(book = item.book)
				elif item.task == 'QA':
					obj = OperationQa.objects.get(book = item.book)
				elif item.task == 'OCR':
					obj = OperationOcr.objects.get(book = item.book)
				dict = {'barcode':item.book.barcode, 'duration':str(item.endTime - item.startTime), 'objects':item.pagesDone, 'user':us, 'isFinished':obj.complete,'rate':int(int(item.pagesDone)/(float(d1_ts-d2_ts)/(60*60))),'task':item.task,'startTime':item.startTime }
            else:
				if item.task == 'Scan':
					obj = OperationScan.objects.get(book = item.book)
				elif item.task == 'QC':
					obj = OperationQc.objects.get(book = item.book)
				elif item.task == 'QA':
					obj = OperationQa.objects.get(book = item.book)
				elif item.task == 'OCR':
					obj = OperationOcr.objects.get(book = item.book)
				dict = {'barcode':item.book.barcode, 'duration':None, 'objects':item.pagesDone, 'user':us, 'isFinished':obj.complete,'rate':int(int(item.pagesDone)/(float(d1_ts-d2_ts)/(60*60))),'task':item.task,'startTime':item.startTime }
            myList.append(dict)

    return render_to_response('data.html', {
                        'list': myList,
                        'user': name,
                 })
def workGraph(request):
    stats = {'name': [], 'rate': []}
    return render_to_response('data.html', {
                        'list': myList,
                        'user': name,
                 })
def logoutUser(request):
    logout(request)
    return render_to_response('Logout.html', {

                 })
