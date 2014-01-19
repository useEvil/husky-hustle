import csv
import pytz
import base64
import random
import logging
import django.contrib.staticfiles
import gdata.photos.service as gdata
import husky.helpers as h
import datetime as date
import json as simplejson
import re as regexp

from django.db import IntegrityError
from django.core import mail
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import password_reset, password_reset_done, password_reset_confirm, password_reset_complete
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.conf import settings

from husky.models import Student, Donation, Teacher, Grade, Album, Photo, Content, Blog, Message, Link, Calendar, ContactForm, DonationForm
from husky.helpers import *

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    c = Context(dict(
        page_title='Home',
        motd=Message.objects.latest('date_added'),
        content=Content.objects.filter(page='index').get(),
        jumbotron=Content.objects.filter(page='jumbotron').get(),
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
        calendar=Calendar().get_events(),
        path=request.path,
    ))
    return render_to_response('index.html', c, context_instance=RequestContext(request))

def nav(request, page='index', id=None):
    c = Context(dict(
        page_title=page.title(),
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
        path=request.path,
        messages=messages.get_messages(request),
    ))
    if page == 'photos':
        c['albums'] = Album()
        c['content'] = Content.objects.filter(page=page).get()
    elif page == 'privacy' or page == 'getting_started':
        c['content'] = Content.objects.filter(page=page).get()
    elif page == 'links':
        c['links'] = Link.objects.filter(status=1).all()
        c['content'] = Content.objects.filter(page=page).get()
    elif page == 'blog':
        if id:
            c['entries'] = [ Blog.objects.get(pk=id) ]
        else:
            c['entries'] = Blog.objects.order_by('-date_added')[:15]
    return render_to_response('%s.html'%page, c, context_instance=RequestContext(request))

def donation_sheet(request, identifier=None, final=None):
    c = Context(dict(
        page_title='Pledge Sheet',
        path=request.path,
        final=final,
    ))
    if identifier and identifier == 'pdf':
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="donation-sheet.pdf"'
        response.write(file("%s/docs/donation_sheet.pdf" % settings.MEDIA_ROOT).read())
        return response
    elif identifier and identifier == 'print':
        c['page_title'] = 'Pledge Sheet'
    elif identifier:
        try:
            c['student'] = Student.objects.get(identifier=identifier)
            c['page_title'] = 'Pledge Sheet: %s' % (c['student'])
        except:
            messages.error(request, 'Could not find Student for identity: %s' % identifier)
    c['messages'] = messages.get_messages(request)
    return render_to_response('account/donation_sheet.html', c, context_instance=RequestContext(request))

def student_donation(request, identifier=None):
    c = Context(dict(
        page_title='Donate',
        path=request.path,
        teachers=Teacher().get_donate_list(),
        make_donation=True,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    if identifier == 'search':
        c['search'] = True
        first_name = request.GET.get('student_first_name') or None
        last_name = request.GET.get('student_last_name') or None
        teacher_name = request.GET.get('teacher_last_name') or None
        if first_name or last_name or teacher_name:
            if first_name and last_name:
                c['search'] = '%s %s' % (first_name, last_name)
            else:
                c['search'] = first_name or last_name or teacher_name
            try:
                c['students'] = Student().find(first_name, last_name, teacher_name)
            except Exception, e:
                messages.error(request, 'Could not find Records matching: %s' % (c['search']))
                c['error'] = True
    elif identifier:
        try:
            c['students'] = Student.objects.get(identifier=identifier)
        except:
            messages.error(request, 'Could not find Student for identity: %s' % identifier)
            c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

def teacher_donation(request, identifier=None):
    c = Context(dict(
        page_title='Donate',
        path=request.path,
        teachers=Teacher().get_list(),
        teachers_donate=Teacher().get_donate_list(),
        teacher_donation=True,
        make_donation=True,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    if not identifier: 
        return render_to_response('donate.html', c, context_instance=RequestContext(request))
    try:
        c['student'] = Student.objects.get(identifier=identifier)
    except:
        messages.error(request, 'Could not find Student for identity: %s' % identifier)
        c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

def payment(request, identifier=None, id=None):
    c = Context(dict(
        page_title='Make a Donation',
        path=request.path,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    try:
        c['student'] = Student.objects.get(identifier=identifier)
    except:
        messages.error(request, 'Could not find Student for identity: %s' % identifier)
        c['error'] = True
    ids = id.split(',')
    if request.GET.get('amount'):
        if request.GET.get('id') and not id: id = request.GET.get('id')
        c['encrypted_block'] = Donation().encrypted_block(Donation().button_data(request.GET.get('amount'), id))
        c['total'] = request.GET.get('amount')
    elif len(ids) > 1:
        total = Donation().get_total(ids)
        c['encrypted_block'] = Donation().encrypted_block(Donation().button_data(total, id))
        c['total'] = total
    else:
        try:
            donation = Donation.objects.get(id=id)
            c['donation'] = donation
            c['encrypted_block'] = donation.encrypted_block()
            c['total'] = donation.total()
        except:
            messages.error(request, 'Could not find Donation for ID: %s' % id)
            c['error'] = True
    c['messages'] = messages.get_messages(request)
    return render_to_response('donation.html', c, context_instance=RequestContext(request))

def donate(request, student_id=None):
    student = Student.objects.get(identifier=student_id)
    from_account = None
    make_donation = None
    teacher_donation = None
    c = Context(dict(
        page_title='Donator',
        path=request.path,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
        teachers=Teacher().get_donate_list(),
        student=student,
        donate=True,
    ))
    if request.POST:
        from_account = request.POST.get('from_account')
        make_donation = request.POST.get('make_donation')
        teacher_donation = request.POST.get('teacher_donation')
        form = DonationForm(request.POST)
        if form.is_valid():
            try:
                donation = Donation(
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email_address=request.POST.get('email_address'),
                    phone_number=request.POST.get('phone_number'),
                    per_lap=request.POST.get('per_lap') or 0,
                    donation=request.POST.get('donation'),
                    date_added=date.datetime.now(pytz.utc),
                    student=student,
                )
                donation.save()
                messages.success(request, from_account and 'Donation Added Successfully' or 'Thank you for making a Pledge')
                c['success'] = True
                c['donate_url'] = student.donate_url()
                c['student_full_name'] = student.full_name()
                c['student_identifier'] = student.identifier
                c['amount'] = donation.donation
                c['full_name'] = donation.full_name()
                c['is_per_lap'] = donation.per_lap
                c['payment_url'] = donation.payment_url()
                c['email_address'] = donation.email_address
                c['subject'] = 'Hicks Canyon Jog-A-Thon: Thank you for making a Pledge'
                c['domain'] = Site.objects.get_current().domain
                if not teacher_donation:
                    _send_email_teamplate('donate', c)
            except Exception, e:
                c['make_donation'] = make_donation or False
                if from_account: c['error'] = True
                messages.error(request, str(e))
        else:
            c['make_donation'] = make_donation or False
            if from_account: c['error'] = True
            messages.error(request, 'Failed to Add %s' % (teacher_donation and 'Donation' or 'Sponsor'))
        c['form'] = form
    c['messages'] = messages.get_messages(request)
    c['teacher_donation'] = teacher_donation or False
    if from_account:
        return HttpResponseRedirect('/account/%s' % student.identifier)
    else:
        return render_to_response('donate.html', c, context_instance=RequestContext(request))

def donate_direct(request):
    make_donation = None
    teacher_donation = None
    c = Context(dict(
        page_title='Donator',
        path=request.path,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
        donate=True,
    ))
    if request.POST:
        make_donation = request.POST.get('make_donation')
        teacher_donation = request.POST.get('teacher_donation')
        form = DonationForm(request.POST)
        if form.is_valid():
            teacher = Teacher.objects.get(pk=request.POST.get('student_teacher_id'))
            first_name = request.POST.get('student_first_name').strip()
            last_name  = request.POST.get('student_last_name').strip()
            identifier = '%s-%s-%s'%(_replace_space(first_name), _replace_space(last_name), teacher.room_number)
            try:
                student = Student.objects.get(identifier=identifier)
            except Exception, e:
                student = Student(
                    first_name=first_name,
                    last_name=last_name,
                    date_added=date.datetime.now(pytz.utc),
                    identifier=identifier,
                    teacher=teacher,
                )
                student.save()
            try:
                donation = Donation(
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email_address=request.POST.get('email_address'),
                    phone_number=request.POST.get('phone_number'),
                    per_lap=request.POST.get('per_lap') or 0,
                    donation=request.POST.get('donation'),
                    date_added=date.datetime.now(pytz.utc),
                    student=student,
                )
                donation.save()
                messages.success(request, 'Thank you for making a Pledge')
                c['success'] = True
                c['donate_url'] = student.donate_url()
                c['student_full_name'] = student.full_name()
                c['student_identifier'] = student.identifier
                c['amount'] = donation.donation
                c['full_name'] = donation.full_name()
                c['is_per_lap'] = donation.per_lap
                c['payment_url'] = donation.payment_url()
                c['email_address'] = donation.email_address
                c['subject'] = 'Hicks Canyon Jog-A-Thon: Thank you for making a Pledge'
                c['domain'] = Site.objects.get_current().domain
                if not teacher_donation:
                    _send_email_teamplate('donate', c)
            except Exception, e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Failed to Add Sponsor')
        c['form'] = form
    c['messages'] = messages.get_messages(request)
    if make_donation and teacher_donation:
        c['teacher_donation'] = True
    return render_to_response('donate.html', c, context_instance=RequestContext(request))

def album(request, album_id=None):
    album = Album().get_album(album_id)
    c = Context(dict(
        page_title=album.title.text,
        path='/nav/photos',
        album=album,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    return render_to_response('photos.html', c, context_instance=RequestContext(request))

def photo(request, album_id=None, photo_id=None):
    album = Album().get_album(album_id)
    photo = Photo().get_photo(album_id, photo_id)
    c = Context(dict(
        page_title=photo.title.text,
        path='/nav/photos',
        photo_album=album,
        photo=photo,
        prev=prevPhoto(album.entry, request.GET.get('index')),
        next=nextPhoto(album.entry, request.GET.get('index')),
        index=int(request.GET.get('index')),
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    return render_to_response('photos.html', c, context_instance=RequestContext(request))

def contact(request):
    c = Context(dict(
        page_title='Contact',
        path=request.path,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender  = form.cleaned_data['sender']
            cc_myself  = form.cleaned_data['cc_myself']
            recipients = [settings.EMAIL_HOST_USER]
            if cc_myself:
                recipients.append(sender)
            mail.send_mail(subject, "%s\n\nSender: %s" % (message, sender), sender, recipients)
            # set message or return json message
            if request.GET.get('format') == 'ajax':
                return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200, 'message': 'Successfully Sent'}), mimetype='application/json')
            else:
                messages.success(request, 'Successfully Sent')
    else:
        form = ContactForm()
    c['form'] = form
    c['messages'] = messages.get_messages(request)
    return render_to_response('contact.html', c, context_instance=RequestContext(request))

def results(request, type=None, grade=None):
    c = Context(dict(
        page_title='Results',
        path='/nav/results',
        type=type or 'all',
        id=request.GET.get('id') or 0,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    if 'admin' in request.path:
        if request.GET.get('id'):
            teacher = Teacher.objects.filter(id=request.GET.get('id')).get()
            donators, sponsors = teacher.get_donations_list()
            c['teacher'] = teacher
            c['donators'] = donators
            c['sponsors'] = sponsors
        if 'verify-paypal-donations' in request.path:
            c['results'] = Donation().verify_paypal_donations(grade)
        elif 'show-unpaid-donations' in request.path:
            c['results'] = Donation().reports_unpaid_donations()
        return render_to_response('admin/results.html', c, context_instance=RequestContext(request))
    else:
        return render_to_response('results.html', c, context_instance=RequestContext(request))

def reporting(request, type=None):
    c = Context(dict(
        page_title='Reporting',
        path=request.path,
        type=type,
        id=request.GET.get('id') or 0,
    ))
    return render_to_response('admin/chart.html', c, context_instance=RequestContext(request))

def emails(request):
    c = Context(dict(
        subject='Hicks Canyon Jog-A-Thon: Help Support %s' % request.POST.get('student_first_name'),
        body=request.POST.get('custom_message'),
        reply_to=settings.EMAIL_HOST_USER,
    ))
    addresses = request.POST.get('email_addresses')
    if not addresses:
        messages.success(request, 'You must provide email addresses')
        return HttpResponse(simplejson.dumps({'result': 'NOTOK', 'status': 400, 'message': 'You must provide email addresses.'}), mimetype='application/json')
    p = regexp.compile(r'\s*,\s*')
    addresses = filter(None, p.split(addresses))
    data = []
    for address in addresses:
        c['email_address'] = address
        data.append(_send_email_teamplate('emails', c, 1))
    _send_mass_mail(data)
    messages.success(request, 'Successfully Sent Emails')
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def reminders(request):
    c = Context(dict(
        subject='Hicks Canyon Jog-A-Thon: Payment Reminder',
        domain=Site.objects.get_current().domain,
        reply_to=settings.EMAIL_HOST_USER,
    ))
    donators = request.POST.getlist('donators')
    if request.POST.get('custom_message'):
        c['custom_message'] = request.POST.get('custom_message')
    data = []
    for donator in donators:
        donation = Donation.objects.get(pk=donator)
        c['name'] = donation.full_name()
        c['email_address'] = donation.email_address
        c['student_name'] = donation.student.full_name()
        c['student_laps'] = donation.student.laps
        c['student_identifier'] = donation.student.identifier
        c['donation_id'] = donation.id
        c['payment_url'] = donation.payment_url()
        data.append(_send_email_teamplate('reminder', c, 1))
    _send_mass_mail(data)
    messages.success(request, 'Successfully Sent Reminders')
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def thanks(request):
    c = Context(dict(
        subject='Hicks Canyon Jog-A-Thon: Thank You',
        domain=Site.objects.get_current().domain,
        reply_to=settings.EMAIL_HOST_USER,
    ))
    donators = request.POST.getlist('donators')
    if request.POST.get('custom_message'):
        c['custom_message'] = request.POST.get('custom_message')
    data = []
    for donator in donators:
        donation = Donation.objects.get(pk=donator)
        c['name'] = donation.full_name()
        c['email_address'] = donation.email_address
        data.append(_send_email_teamplate('thanks', c, 1))
    _send_mass_mail(data)
    messages.success(request, 'Successfully Sent Thank You Emails')
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

@csrf_exempt
def paid(request, donation_id=None):
    c = Context(dict(
        subject='Hicks Canyon Jog-A-Thon: Payment Received',
        email_address=settings.EMAIL_HOST_USER,
    ))
    result = None
    query  = request.POST and request.POST.urlencode() or request.GET.urlencode() or None
    if query:
        try:
            result = getHttpRequest(settings.PAYPAL_IPN_URL, 'cmd=_notify-validate&%s' % query)
        except Exception, e:
            printLog('Failed IPN handshake')
    if result == 'VERIFIED':
        data = []
        for id in donation_id.split(','):
            try:
                object = Donation.objects.get(pk=id)
                object.paid = True
                object.donated = object.total()
                object.save()
                messages.success(request, 'Successfully set Sponsor to Paid')
                c['code'] = result
                c['query'] = query
                c['name'] = object.full_name()
                c['amount'] = object.donated
                data.append(_send_email_teamplate('paid', c, 1))
            except Exception, e:
                messages.error(request, 'Failed to set Sponsor to Paid: %s' % str(e))
        _send_mass_mail(data)
    elif result:
        c['code'] = result
        c['query'] = query
        c['name'] = 'Sponsor Name'
        c['amount'] = '0.00'
        c['subject'] = 'Hicks Canyon Jog-A-Thon: Payment Failed'
        _send_email_teamplate('paid', c)
    elif regexp.match('[^\d,]+', donation_id):
        messages.success(request, 'Successfully Received Payment')
    else:
        for id in donation_id.split(','):
            try:
                object = Donation.objects.get(pk=id)
                object.paid = True
                object.donated = object.total()
                object.save()
                messages.success(request, 'Successfully set Sponsor to Paid')
            except Exception, e:
                messages.error(request, 'Failed to set Sponsor to Paid: %s' % str(e))
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200, 'code': result}), mimetype='application/json')

@csrf_exempt
def thank_you(request, donation_id=None):
    c = Context(dict(
        page_title='Thank You',
        path=request.path,
        bar_height=Donation().bar_height(),
        arrow_height=Donation().arrow_height(),
    ))
    if donation_id:
        try:
            object = Donation.objects.get(pk=donation_id)
            object.paid = True
            object.save()
            messages.success(request, 'Successfully set Sponsor to Paid')
        except Exception, e:
            messages.error(request, 'Failed to set Sponsor to Paid: %s' % str(e))
    elif request.GET.get('custom') or request.POST.get('custom'):
        donation_id = request.GET.get('custom')
        try:
            object = Donation.objects.get(pk=donation_id)
            object.paid = True
            object.save()
            messages.success(request, 'Successfully set Sponsor to Paid')
        except Exception, e:
            messages.error(request, 'Failed to set Sponsor to Paid: %s' % str(e))
    else:
        return render_to_response('thank_you.html', c, context_instance=RequestContext(request))
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

@csrf_protect
def reset(request):
    return password_reset(request, template_name='registration/reset_password.html')

def reset_done(request):
    return password_reset_done(request, template_name='registration/reset_password_done.html')

@sensitive_post_parameters()
@never_cache
def reset_confirm(request, uidb36=None, token=None):
    return password_reset_confirm(request, uidb36, token, template_name='registration/reset_password_confirm.html')

def reset_complete(request):
    return password_reset_complete(request, template_name='registration/reset_password_complete.html')

@never_cache
def json(request, student_id=None):
    offset = request.GET.get('page') or 1
    limit = request.GET.get('rp')  or 30
    query = request.GET.get('query')  or None
    field = request.GET.get('qtype')  or None
    sortname = request.GET.get('sortname')  or 'id'
    sortorder = request.GET.get('sortorder') or 'asc'
    students = [student_id]
    offset = int(offset) - 1
    offset = offset * int(limit)
    donations = Donation().get_donations(students, limit, offset, query, field, sortname, sortorder)
    total = Donation().get_donations_total(students, query, field)
    data = _formatData(donations, total)
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def reports(request, type=None):
    json = {}
    if type == 'totals-by-grade':
        json = Donation().reports_totals_by_grade()
    elif type == 'most-laps-by-grade':
        json = Donation().reports_most_laps_by_grade()
    elif type == 'most-laps-by-grade-avg':
        json = Donation().reports_most_laps_by_grade_avg()
    elif type == 'most-laps-by-student-by-grade':
        json = Donation().reports_most_laps_by_student_by_grade()
    elif type == 'most-laps-by-student-by-grade-girls':
        json = Donation().reports_most_laps_by_student_by_grade('F')
    elif type == 'most-laps-by-student-by-grade-boys':
        json = Donation().reports_most_laps_by_student_by_grade('M')
    elif type == 'most-donations-by-grade':
        json = Donation().reports_most_donations_by_grade()
    elif type == 'most-donations-by-grade-avg':
        json = Donation().reports_most_donations_by_grade_avg()
    elif type == 'most-donations-by-student':
        json = Donation().reports_most_donations_by_student()
    elif type == 'most-donations-by-student-pledged':
        json = Donation().reports_most_donations_by_student_pledged()
    elif type == 'most-donations-by-day-by-sponsor':
        json = Donation().reports_most_donations_by_day_by_sponsor()
    elif type == 'most-donations-by-day':
        json = Donation().reports_most_donations_by_day()
    elif type == 'most-donations-by-student-by-grade':
        json = Donation().reports_most_donations_by_student_by_grade()
    elif type == 'donations-by-teacher':
        id = int(request.GET.get('id') or 0)
        json = Donation().reports_donations_by_teacher(id)
    elif type == 'download-raffle-tickets':
        winner = request.GET.get('winner') or None
        teacher = request.GET.get('teacher') or None
        students = Student().get_collected_list()
        teachers = Teacher().get_donate_list()
        if teacher:
            tickets = []
            for teach in teachers:
                tickets.append(teach.full_name())
            random.shuffle(tickets)
            json['winner'] = random.choice(tickets)
        elif winstudentner:
            tickets = []
            for student in students:
                for n in range(student.total_raffle_tickets()):
                    tickets.append(student.full_name())
            random.shuffle(tickets)
            json['winner'] = random.choice(tickets)
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="raffle-tickets.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'Student First Name', 'Student Last Name', 'Teacher', 'Total Collected', 'Total Raffle Tickets'])
            for student in students:
                writer.writerow([student.id, student.first_name, student.last_name, student.teacher, student.collected, student.total_raffle_tickets()])
            return response
    return HttpResponse(simplejson.dumps(json), mimetype='application/json')

def send_teacher_reports(request, id=None):
    c = Context(dict(
        subject='Hicks Canyon Jog-A-Thon: Sponsor List',
        reply_to=settings.EMAIL_HOST_USER,
    ))
    ## check donations for each Teacher ##
    if id:
        ids = id.split(',')
        teachers = Teacher.objects.filter(id__in=ids).all()
    else:
        teachers = Teacher.objects.exclude(list_type=2).all()
    data = []
    for teacher in teachers:
        sponsors = []
        c['teacher_name'] = teacher.full_name()
        c['email_address'] = settings.DEBUG and settings.EMAIL_HOST_USER or teacher.email_address
        donations = Donation.objects.filter(first_name__contains=teacher.last_name).order_by('student__last_name', 'student__first_name')
        for donation in donations:
            full_name = donation.student.full_name()
            if full_name not in sponsors:
                sponsors.append(full_name)
        if len(sponsors) > 0:
            c['sponsors'] = sponsors
            data.append(_send_email_teamplate('reports-teacher', c, 1))
    ## check donations for Mrs. Agopian ##
    donations = Donation.objects.filter(first_name__contains='Agopian').order_by('student__last_name', 'student__first_name')
    sponsors = []
    for donation in donations:
        full_name = donation.student.full_name()
        if full_name not in sponsors:
            sponsors.append(full_name)
    if len(sponsors) > 0:
        c['sponsors'] = sponsors
        c['teacher_name'] = 'Mrs. Agopian'
        c['email_address'] = settings.DEBUG and settings.EMAIL_HOST_USER or 'cagopian@tustin.k12.ca.us'
        data.append(_send_email_teamplate('reports-teacher', c, 1))
    _send_mass_mail(data)
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def send_unpaid_reports(request):
    c = Context(dict(
        subject='Hicks Canyon Jog-A-Thon: Unpaid Report',
        reply_to=settings.EMAIL_HOST_USER,
        email_address=settings.EMAIL_HOST_USER,
    ))
    donations = Donation.objects.exclude(paid=1).order_by('student__last_name', 'student__first_name')
    data = []
    sponsors  = {}
    for donation in donations:
        full_name = donation.student.full_name()
        if not sponsors.has_key(full_name):
            sponsors[full_name] = []
        sponsors[full_name].append(donation)
    if len(sponsors) > 0:
        c['sponsors'] = sponsors
        data.append(_send_email_teamplate('reports-unpaid', c, 1))
    _send_mass_mail(data)
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')

def send_unpaid_reminders(request, type=None, donation_id=None):
    c = Context(dict(
        subject='Hicks Canyon Jog-A-Thon: Pledge Reminder',
        reply_to=settings.EMAIL_HOST_USER,
    ))
    if donation_id:
        donations = [Donation.objects.filter(id=donation_id).order_by('student__last_name', 'student__first_name').get()]
    elif type:
        flag = type == 'per_lap' and 1 or 0
        donations = Donation.objects.filter(per_lap=flag).exclude(paid=1).order_by('student__last_name', 'student__first_name')
    else:
        donations = Donation.objects.exclude(paid=1).order_by('student__last_name', 'student__first_name')
    data = []
    sponsors = {}
    for donation in donations:
        email_address = donation.email_address
        if regexp.match('^(_teacher_)', email_address): continue
        if not sponsors.has_key(email_address):
            sponsors[email_address] = []
        sponsors[email_address].append(donation)
    for email, donations in iter(sponsors.iteritems()):
        donation = donations[0]
        ids = ','.join(str(d.id) for d in donations)
        c['name'] = donation.full_name()
        c['email_address'] = settings.DEBUG and settings.EMAIL_HOST_USER or email
        c['student_name'] = donation.student.full_name()
        c['student_laps'] = donation.student.laps
        c['student_identifier'] = donation.student.identifier
        c['donation_id'] = donation.id
        c['payment_url'] = donation.payment_url(ids)
        data.append(_send_email_teamplate('reminder', c, 1))
        if settings.DEBUG: break
    _send_mass_mail(data)
    messages.success(request, 'Successfully Sent Reminders')
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200, 'count': len(data)}), mimetype='application/json')

def calculate_totals(request, type=None, id=None):
    if type == 'donation':
        Donation().calculate_totals(id)
    if type == 'student':
        Student().calculate_totals(id)
    if type == 'both':
        Donation().calculate_totals()
        Student().calculate_totals()
    return HttpResponse(simplejson.dumps({'result': 'OK', 'status': 200}), mimetype='application/json')


def _formatData(data, total):
    if not data and not total: return
    result = { }
    funds = 0
    count = 1
    result['rows'] = [ ]
    result['total'] = total
    for donation in data:
        row = {'id': donation.id, 'cell': [ donation.id ]}
        if donation.last_name == 'teacher':
            row['cell'].append(donation.first_name)
            row['cell'].append('<span class="hidden">%s</span>' % donation.last_name)
            row['cell'].append('<span class="hidden">%s</span>' % donation.email_address)
            row['cell'].append('<span class="hidden">%s</span>' % donation.phone_number)
            row['cell'].append(donation.date_added.strftime('%m/%d/%Y'))
            row['cell'].append('<span class="hidden">0</span>')
        else:
            row['cell'].append(donation.paid and donation.first_name or '<a href="#" class="show-edit" id="edit_sponsor_%s">%s</a>' % (donation.id, donation.first_name))
            row['cell'].append(donation.last_name)
            row['cell'].append(donation.email_address)
            row['cell'].append(donation.phone_number)
            row['cell'].append(donation.date_added.strftime('%m/%d/%Y'))
            row['cell'].append(donation.student.laps or 0)
        row['cell'].append("%01.2f" % (donation.donation or 0))
        row['cell'].append('<span abbr="total">%01.2f</span>' % (donation.total()))
        if donation.last_name == 'teacher':
            row['cell'].append('<span class="hidden">no</span>')
        else:
            row['cell'].append(donation.per_lap and 'yes' or 'no')
        row['cell'].append(donation.paid and '<span class="success">Paid</span>' or '<input type="checkbox" value="paid" name="paid" id="paid-%s" class="set-paid" title="If your Sponsor has paid you, you can mark their Donation as Paid." />' % donation.id)
        row['cell'].append('<input type="checkbox" value="%s" name="reminder" id="reminder-%s" class="set-reminder" />' % (donation.id, donation.id))
        result['rows'].append(row)
        count += 1
        funds += donation.total()
    result['rows'].append({'id': None, 'cell': [ 'Total', None, None, None, None, None, None, "%01.2f" % (funds), None, None, None, None ]})
    return result

def _send_email_teamplate(template, data, mass=None):
    if data.has_key('body'):
        body = data['body']
    else:
        t = loader.get_template('email/%s.txt' % template)
        body = t.render(data)
    if mass:
        return mail.EmailMessage(data['subject'], body, settings.EMAIL_HOST_USER, [data['email_address']], headers={'Reply-To': data['reply_to']})
    else:
        mail.send_mail(data['subject'], body, settings.EMAIL_HOST_USER, [data['email_address']])

def _send_mass_mail(messages):
    connection = mail.get_connection()
    connection.send_messages(messages)

def _replace_space(string):
     # Replace all runs of whitespace with a single dash
     string = regexp.sub(r"\s+", '-', string.lower())

     return string

class BlogFeed(Feed):
    title = "Husky Hustle Site News"
    link  = "/nav/blog/"
    description = "Updates on changes and additions to huskyhustle.com."

    def items(self):
        return Blog.objects.order_by('-date_added')[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_author_name(self, item):
        return item.author

    def item_pubdate(self, item):
        return item.date_added

    def item_link(self, item):
        domain = Site.objects.get_current().domain
        return 'http://%s/nav/blog/%d' % (domain, item.id)

