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
    #if request.user.is_authenticated():
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
    users = list(User.objects.all())
    myList = []
    for item in users:
        us = item.username
        myList.append(us)
    return render_to_response('admin_login.html', {
            'list':myList,
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
        b =None
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
                b = Book.objects.create(barcode=bar, totalPages=pages)
                b.save()
                msg = 'Book object with barcode '+ bar + ' created successfully'
                return render_to_response('processingForm.html', {
                        'msg': msg,
                        'form' : ProcessingForm(initial={'book': b,
                                                        'user': request.user}),
                },context_instance=RequestContext(request))

            elif book is not None and book.bookComplete == True:
                msg = 'Book with barcode ' + bar + 'is already done'
                return render_to_response('message.html', {
                        'msg': msg,
                },context_instance=RequestContext(request))
            elif book is not None and book.bookComplete == False:
                msg = 'Book with barcode ' + bar + 'was partially done'
                return render_to_response('processingForm.html', {
                        'msg': msg,
                        'form' : ProcessingForm(initial={'book': book,
                                                        'user': request.user}),
                },context_instance=RequestContext(request))
            elif book is not None and book.bookComplete is None:
                msg = 'Book with barcode ' + bar + 'is not done'
                return render_to_response('processingForm.html', {
                        'msg': msg,
                        'form' : ProcessingForm(initial={'book': book,
                                                        'user': request.user}),
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
            book = Book.objects.get(id = bookid)
            list = ProcessingSession.objects.filter(book=book)
            pagecount = 0
            for item in list:
                pagecount = pagecount + item.pagesDone
            pagecount = pagecount + int(request.POST['pagesDone'])
            if pagecount == book.totalPages:
                book.bookComplete = True
                book.save()
            else:
                book.bookComplete = False
                book.save()
            pages = request.POST['pagesDone']
            comm = request.POST['comments']
            openingDate = request.POST['startTime']
            closingDate = request.POST['endTime']
            tasktype = request.POST['task']
            bst = None
            bst = ProcessingSession(book=Book.objects.get(id =request.POST['book']),user=User.objects.get(id=request.POST['user']),pagesDone=pages,comments=comm,startTime=openingDate,endTime=closingDate,task=tasktype)
            bst.save()
            return render_to_response('pages.html', {
                        'pages' : pages,
                        'comments' : comm,
                        'openingDate' : openingDate,
                        'closingDate' : closingDate,
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
        seq = None

        for item in b:
            fmt = '%Y-%m-%d %H:%M:%S'
            d1 = datetime.strptime(str(item.endTime),fmt)
            d2 = datetime.strptime(str(item.startTime),fmt)
            d1_ts = time.mktime(d1.timetuple())
            d2_ts = time.mktime(d2.timetuple())
            if item.endTime is not None:
                seq = (item.book.barcode, str(item.endTime - item.startTime), item.pagesDone, name, item.book.bookComplete,int(int(item.pagesDone)/(float(d1_ts-d2_ts)/(60*60))),item.task,item.startTime )
            else:
                seq = (item.book.barcode, None , item.pagesDone , name, item.book.bookComplete,int(int(item.pagesDone)/(float(d1_ts-d2_ts)/(60*60))),item.task,item.startTime)
            myList.append(seq)
    else:
        b = ProcessingSession.objects.all();
        seq = None
        for item in b:
            us = item.user.username
            fmt = '%Y-%m-%d %H:%M:%S'
            d1 = datetime.strptime(str(item.book.end_time),fmt)
            d2 = datetime.strptime(str(item.book.start_time),fmt)
            d1_ts = time.mktime(d1.timetuple())
            d2_ts = time.mktime(d2.timetuple())
            if item.book.end_time is not None:
                seq = (item.book.barcode, str(item.book.end_time - item.book.start_time), item.pages, us, item.book_complete,int(int(item.pages)/(float(d1_ts-d2_ts)/(60*60))),item.book.task )
            else:
                seq = (item.book.barcode, None , item.pages , us, item.book_complete,int(int(item.pages)/(float(d1_ts-d2_ts)/(60*60))),item.book.task)
            myList.append(seq)

    return render_to_response('data.html', {
                        'list': myList,
                        'user': name,
                 })
def logoutUser(request):
    logout(request)
    return render_to_response('Logout.html', {

                 })