import os, csv, pytz, math, base64, urllib, logging

import re as regex
import datetime as date
import husky.bitly as bitly
import gdata.media as media
import gdata.photos.service as gdata
import gdata.calendar.client as cdata

from django.db import models
from django.db.models import Count, Sum, Avg, Max
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.models import Site
from django import forms

from paypal import PayPal
from picasa import  PicasaField, PicasaStorage
from decimal import Decimal

from husky.helpers import *
# from husky.signals import *

logger = logging.getLogger(__name__)

# Field Classes
class CurrencyField(models.DecimalField):

    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] =  10
        kwargs['decimal_places'] = 2
        super(CurrencyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        try:
            return super(CurrencyField, self).to_python(value).quantize(Decimal('0.01'))
        except AttributeError:
            return None


# Google Classes
# class GoogleCalendarConnect(object):
# 
#     gd_client = cdata.CalendarClient(source=settings.PICASA_STORAGE_OPTIONS['source'])
#     gd_client.ClientLogin(settings.PICASA_STORAGE_OPTIONS['email'], settings.PICASA_STORAGE_OPTIONS['password'], gd_client.source)
# 
#     def client(self):
#         return self.gd_client


class GooglePhotoConnect(object):

    gd_client = gdata.PhotosService()
    gd_client.email = settings.PICASA_STORAGE_OPTIONS['email']
    gd_client.password = settings.PICASA_STORAGE_OPTIONS['password']
    gd_client.source = settings.PICASA_STORAGE_OPTIONS['source']
    gd_client.ProgrammaticLogin()

    def client(self):
        return self.gd_client


# class CalendarGoogle(object):
# 
#     gd_client = GoogleCalendarConnect().client()
# 
#     def get_events(self):
#         query = cdata.CalendarEventQuery()
#         query.start_min = date.datetime.now(pytz.utc).strftime('%Y-%m-%d')
#         query.start_max = (date.datetime.now(pytz.utc) + date.timedelta(days=14)).strftime('%Y-%m-%d')
#         feed = self.gd_client.GetCalendarEventFeed(q=query, visibility='public', sortorder='ascending', orderby='starttime')
#         return feed


class Calendar(models.Model):

    title = models.CharField(max_length=100)
    content = models.TextField(max_length=65000, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_of_event = models.DateTimeField(auto_now_add=False)
    duration = models.CharField(max_length=25, blank=True, null=True, verbose_name="Duration (ie. 1 hour)")

    def get_events(self):
        start_min = date.datetime.now(pytz.utc).strftime('%Y-%m-%d')
        start_max = (date.datetime.now(pytz.utc) + date.timedelta(days=144)).strftime('%Y-%m-%d')
        feed = Calendar.objects.filter(date_of_event__gt=start_min, date_of_event__lte=start_max)
        return feed.order_by('date_of_event').all()


class Photo(object):

    gd_client = GooglePhotoConnect().client()

    def get_photo(self, album_id=None, photo_id=None):
        if not photo_id or not photo_id: return
        photo = self.gd_client.GetFeed('/data/feed/api/user/default/albumid/{0}/photoid/{1}'.format(album_id, photo_id))
        return photo

    def get_photos(self, album_id=None):
        if not album_id: return
        photos = self.gd_client.GetFeed('/data/feed/api/user/default/albumid/{0}?kind=photo'.format(album_id))
        return photos

    def get_photos_by_tags(self, tags='huskyhustle'):
        photos = self.gd_client.GetFeed('/data/feed/api/all?kind=photo&tag={0}'.format(tags))
        return photos


class Album(object):

    gd_client = GooglePhotoConnect().client()

    def get_album(self, album_id=None):
        if not album_id: return
        photos = Photo().get_photos(album_id)
        return photos

    def get_albums(self):
        albums = self.gd_client.GetUserFeed(user=settings.PICASA_STORAGE_OPTIONS['userid'])
        return albums


# Create your models here.
class Content(models.Model):

    page = models.CharField(max_length=100)
    content = models.TextField(max_length=65000, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)


class Blog(models.Model):

    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    content = models.TextField(max_length=4000)
    date_added = models.DateTimeField(auto_now_add=True)


class Message(models.Model):

    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    content = models.TextField(max_length=4000)
    date_added = models.DateTimeField(auto_now_add=True)


class Link(models.Model):

    title = models.CharField(max_length=50)
    url = models.CharField(max_length=255)
    shorten = models.CharField(max_length=255)
    status = models.IntegerField(blank=True, null=True, choices=((0,0), (1,1)))

    def __unicode__(self):
        return self.title

    def shortened(self):
        if not self.shorten:
            api = bitly.Api(login=settings.BITLY_LOGIN, apikey=settings.BITLY_APIKEY)
            self.shorten = api.shorten(self.url)
            self.save()
        return self.shorten


class Grade(models.Model):

    grade = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=15)

    def __unicode__(self):
        return self.title

    def get_all(self):
        return Grade.objects.exclude(grade=-1).all()

    def most_donations_avg(self):
        if not self.total_students(): return 0
        avg = self.total_collected() / self.total_students()
        return round(avg, 2)

    def most_laps_avg(self):
        if not self.total_students(): return 0
        avg = float(self.total_laps()) / self.total_students()
        return round(avg, 2)

    def total_students(self):
        return Student.objects.filter(teacher__grade=self).count()

    def total_laps(self):
        results = Student.objects.filter(teacher__grade=self).exclude(disqualify=True).aggregate(num_laps=Sum('laps'))
        return results['num_laps'] or 0

    def total_donations(self):
        results = Donation.objects.filter(student__teacher__grade=self).aggregate(total_donations=Sum('donated'))
        return float(results['total_donations'] or 0)

    def total_collected(self):
        results = Student.objects.filter(teacher__grade=self).aggregate(total_collected=Sum('collected'))
        return float(results['total_collected'] or 0)

    def percent_completed(self):
        percentage = 0
        if self.total_collected() and self.total_donations():
            percentage = self.total_collected() / self.total_donations()
        return round(percentage, 3)


class Teacher(models.Model):

    title = models.CharField(max_length=5, choices=(('Mrs.', 'Mrs.'), ('Ms.', 'Ms.'), ('Miss', 'Miss'), ('Mr.', 'Mr.')), default='Mrs.')
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=25, blank=True, null=True, default='(714) 734-1878')
    room_number = models.CharField(max_length=5)
    website = models.CharField(max_length=255, blank=True, null=True)
    shorten = models.CharField(max_length=255, blank=True, null=True)
    grade = models.ForeignKey(Grade, related_name='teachers')
    list_type = models.IntegerField(blank=True, null=True)
    class Meta:
        ordering = ['last_name', 'first_name']

    def __unicode__(self):
        return '{0} ({1}) {2}'.format(self.full_name(), self.room_number, self.grade)

    def full_name(self):
        return '{0} {1} {2}'.format(self.title, self.first_name, self.last_name)

    def title_name(self):
        return '{0} {1}'.format(self.title, self.last_name)

    def find(self, last_name=None):
        try:
            return Teacher.objects.filter(last_name__icontains=last_name).all()
        except ObjectDoesNotExist, e:
            return

    def total_students(self, exclude=None):
        if exclude and exclude == 1:
            return Student.objects.filter(teacher=self, laps__gt=0).exclude(disqualify=True).count()
        elif exclude and exclude == 2:
            return Student.objects.filter(teacher=self, collected__gt=0).count()
        else:
            return Student.objects.filter(teacher=self).count()

    def total_participation(self):
        return Student.objects.filter(teacher=self, collected__gt=0).count()

    def get_all(self):
        return Teacher.objects.exclude(grade__grade=-1).all()

    def get_donate_list(self):
        return Teacher.objects.exclude(list_type=2).order_by('grade','room_number').all()

    def get_list(self):
        return Teacher.objects.exclude(list_type=3).order_by('grade','room_number').all()

    def get_donations(self):
        total = Donation.objects.filter(student__teacher=self).aggregate(donated=Sum('donated'))
        return float(total['donated'] or 0)

    def get_donations_list(self):
        donators = []
        sponsors = []
        students = Student.objects.filter(teacher=self).all()
        for student in students:
            donation = student.total_sum()
            donators.append({'name': student.full_name(), 'total': float(donation['total_sum'] or 0)})
        donations = Donation.objects.filter(first_name__contains=self.last_name)
        totals = { }
        for index, donation in enumerate(donations):
            full_name = donation.student.list_name()
            if totals.has_key(full_name):
                totals[full_name] += donation.donated or 0
            else:
                totals[full_name] = donation.donated or 0
        for student, total in iter(sorted(totals.iteritems())):
            sponsors.append({'name': student, 'total': float(total or 0)})
        return donators, sponsors

    def donate_url(self, identifier=None):
        if not identifier: return
        site = Site.objects.get_current()
        donate_url = 'http://{0}/teacher-donation/{1}'.format(site.domain, identifier)
        return donate_url

    def shortened(self):
        if not self.shorten:
            api = bitly.Api(login=settings.BITLY_LOGIN, apikey=settings.BITLY_APIKEY)
            self.shorten = api.shorten(self.website)
            self.save()
        return self.shorten

    def reports_url(self):
        site = Site.objects.get_current()
        reports_url = 'http://{0}/admin/results/donations-by-teacher?id={1}'.format(site.domain, self.id)
        return reports_url


class Student(models.Model):

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    identifier = models.CharField(max_length=100, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)
    laps = models.IntegerField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True, choices=(('M', 'Boy'), ('F', 'Girl')))
    collected = CurrencyField(blank=True, null=True)
    disqualify = models.IntegerField(default=0, choices=((0, 'No'), (1, 'Yes')))
    pledged = CurrencyField(blank=True, null=True)
    teacher = models.ForeignKey(Teacher, related_name='students')

    class Meta:
        ordering = ['last_name', 'first_name', 'teacher']

    def __unicode__(self):
        return self.select_list_name()

    def form_list_name(self):
        return '{0}, {1}; {2}'.format(self.last_name, self.first_name, self.teacher)

    def select_list_name(self):
        return '{0}, {1}; {2}'.format(self.last_name, self.first_name, self.identifier)

    def list_name(self):
        return '{0}, {1}'.format(self.last_name, self.first_name)

    def full_name(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

    def find(self, first_name=None, last_name=None, teacher_name=None):
        try:
            if first_name and last_name:
                return Student.objects.filter(first_name__icontains=first_name, last_name__icontains=last_name).distinct().all()
            elif first_name:
                return Student.objects.filter(first_name__icontains=first_name).distinct().all()
            elif last_name:
                return Student.objects.filter(last_name__icontains=last_name).distinct().all()
            elif teacher_name:
                return Student.objects.filter(teacher__last_name__icontains=teacher_name).distinct().all()
        except ObjectDoesNotExist, e:
            logger.debug('==== e [{0}]'.format(e))
            return

    @property
    def get_identifier(self):
        identifier = '{0}-{1}-{2}'.format(self.first_name, self.last_name, self.teacher.room_number)
        identifier = regex.sub(r'^(\s+|\s+)$', '', identifier)
        identifier = regex.sub(r'(\.+)', '-', identifier)
        identifier = regex.sub(r'(\s+)', '-', identifier)
        identifier = regex.sub(r'(-+)', '-', identifier)
        return identifier.lower()

    def get_collected_list(self):
        return Student.objects.filter(collected__gt=0).order_by('-collected').all()

    def student_url(self):
        return self.set_url('student')

    def donation_sheet_url(self):
        return self.set_url('donation-sheet')

    def invitation_url(self):
        return self.set_url('invite')

    def payment_url(self):
        return self.set_url('make-payment')

    def donate_url(self):
        return self.set_url('student-donation')

    def donate_teacher_url(self):
        return self.set_url('teacher-donation')

    def manage_url(self):
        return self.set_url('account')

    def reminder_url(self):
        return self.set_url('reminders')

    def order_form_url(self):
        return self.set_url('order')

    def set_url(self, page=None):
        site = Site.objects.get_current()
        return 'http://{0}/{1}/{2}'.format(site.domain, page, self.identifier)

    def facebook_share_url(self):
        site = Site.objects.get_current()
        params = 'app_id={0}&link={1}&picture=http://{2}/static/images/hickslogo-1.jpg&name={3}&caption={4}&description={5}&redirect_uri=http://{2}/'.format(
            settings.FACEBOOK_APP_ID,
            self.donate_url(),
            site.domain,
            urllib.quote('Husky Hustle'),
            urllib.quote('Donate to {0}'.format(self.full_name())),
            urllib.quote("Donate and help further our student's education.")
        )
        return 'https://www.facebook.com/dialog/feed?' + params

    def twitter_share_url(self):
        return 'https://twitter.com/intent/tweet?button_hashtag=HuskyHustle&url={0}'.format(self.donate_url())

    def google_share_url(self):
        return 'https://plus.google.com/share?url={0}'.format(self.donate_url())

    def grades(self):
        return Grade.objects.all()

    def teachers(self):
        return Teacher.objects.filter(grade=self.teacher.grade).all()

    def donations(self):
        return Donation.objects.filter(student=self).count()

    def sponsors_flat(self):
        return Donation.objects.filter(student=self, per_lap=False).exclude(type__in=[1,2]).all()

    def sponsors_perlap(self):
        return Donation.objects.filter(student=self, per_lap=True).all()

    def sponsors_teacher(self):
        return Donation.objects.filter(student=self, type__in=[1,2]).all()

    def sponsored_principal(self):
        try:
            return Donation.objects.filter(student=self, type=2).get()
        except ObjectDoesNotExist, e:
            return

    def total_sum(self):
        return Donation.objects.filter(student=self).aggregate(total_sum=Sum('donated'))

    def total_for_laps(self):
        total_due = 0
        for sponsor in self.sponsors_perlap():
            total_due += sponsor.total() or 0
        return total_due

    def total_for_flat(self):
        total_due = 0
        for sponsor in self.sponsors_flat():
            total_due += sponsor.total() or 0
        return total_due

    def total_for_sponsors(self):
        total_due = 0
        for sponsor in self.sponsors_teacher():
            total_due += sponsor.total() or 0
        return total_due

    def total_raffle_tickets(self):
        if not self.collected: return 0
        tickets = int(self.collected / settings.RAFFLE_TICKET_AMT)
        return tickets

    def total_due(self):
        total_due = 0
        for sponsor in self.sponsors_flat():
            if not sponsor.paid:
                total_due += sponsor.total() or 0
        for sponsor in self.sponsors_perlap():
            if not sponsor.paid:
                total_due += sponsor.total() or 0
        for sponsor in self.sponsors_teacher():
            if not sponsor.paid:
                total_due += sponsor.total() or 0
        return total_due

    def total_collected(self):
        total_collected = 0
        for sponsor in self.sponsors_flat():
            if sponsor.paid:
                total_collected += sponsor.total() or 0
        for sponsor in self.sponsors_perlap():
            if sponsor.paid:
                total_collected += sponsor.total() or 0
        for sponsor in self.sponsors_teacher():
            if sponsor.paid:
                total_collected += sponsor.total() or 0
        return total_collected

    def grand_totals(self):
        total_due = self.total_due()
        total_got = self.total_collected()
        return [total_got, total_due, (total_due + total_got)]

    def calculate_totals(self, id=None):
        if id:
            student = (self.id == id) and self or Student.objects.get(pk=id)
            total_collected = 0
            total_pledged = 0
            for sponsor in student.sponsors.all():
                total_pledged += sponsor.total() or 0
                if sponsor.paid:
                    total_collected += sponsor.total() or 0
            self.collected = total_collected
            self.pledged = total_pledged
            self.save()
        else:
            students = Student.objects.all()
            for student in students:
                total_collected = 0
                total_pledged = 0
                for sponsor in student.sponsors.all():
                    total_pledged += sponsor.total() or 0
                    if sponsor.paid:
                        total_collected += sponsor.total() or 0
                student.collected = total_collected
                student.pledged = total_pledged
                student.save()


class Donation(models.Model):

    TYPES = (
        (0, 'student'),
        (1, 'teacher'),
        (2, 'principal'),
    )
    PAID_BY = (
        ('cash','cash'),
        ('check','check'),
        ('online','online'),
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email_address = models.CharField(max_length=100, default='_sponsor_@huskyhustle.com')
    phone_number = models.CharField(max_length=25, blank=True, null=True)
    student = models.ForeignKey(Student, related_name='sponsors')
    donation = CurrencyField(blank=True, null=True)
    donated = CurrencyField(blank=True, null=True)
    per_lap = models.BooleanField(null=False, default=False)
    paid = models.BooleanField(null=False, default=0)
    paid_by = models.CharField(max_length=6, blank=True, null=True, default='online', choices=PAID_BY)
    type = models.IntegerField(null=False, default=0, choices=TYPES)
    date_added = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['last_name', 'first_name']

    def __unicode__(self):
        return '{0}: [{1}]'.format(self.full_name(), self.id)

    def save(self, *args, **kwargs):
        if self.paid:
            self.donated = self.total() or 0
        super(Donation, self).save(*args, **kwargs)
        if not self.pledges.exists():
            pledge = Pledge.objects.create(
                email_address=self.email_address,
                donation=self,
            )

    def full_name(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

    def laps(self):
        return self.student.laps or 0

    def teacher(self):
        return self.student.teacher or ''

    def type_display(self):
        d = dict(self.TYPES)
        if self.type in d:
            return d[self.type]

    def total(self):
        if self.per_lap:
           amount = self.donation * (self.student.laps or 0)
           return CurrencyField().to_python(amount)
        else:
            return CurrencyField().to_python(self.donation)

    def bar_height(self):
        try:
            results = Donation.objects.all().aggregate(donated=Sum('donated'))
            total   = results['donated'] or 0
            percentage = total / settings.DONATION_GOAL
            return int(settings.MAX_BAR_LENGTH * percentage)
        except:
            return 0

    def arrow_height(self):
        try:
            results = Donation.objects.filter(paid=True).aggregate(donated=Sum('donated'))
            total   = results['donated'] or 0
            percentage = total / settings.DONATION_GOAL
            return int((settings.MAX_ARROW_HEIGHT * percentage) + settings.BASE_ARROW_HEIGHT)
        except:
            return settings.BASE_ARROW_HEIGHT

    def get_donations(self, student, limit=30, offset=0, query=None, field='id', sortname='id', sortorder='asc'):
        results = []
        try:
            limited = int(limit) + int(offset)
            if sortorder == 'desc':
                sortname = '-{0}'.format(sortname)
            if query:
                if field == 'last_name':
                    results = Donation.objects.filter(student__identifier__in=student, last_name__contains=query).order_by(sortname)[offset:limited]
                elif field == 'first_name':
                    results = Donation.objects.filter(student__identifier__in=student, first_name__contains=query).order_by(sortname)[offset:limited]
                elif field == 'email_address':
                    results = Donation.objects.filter(student__identifier__in=student, email_address__contains=query).order_by(sortname)[offset:limited]
                elif field == 'phone_number':
                    results = Donation.objects.filter(student__identifier__in=student, phone_number__contains=query).order_by(sortname)[offset:limited]
                else:
                    results = Donation.objects.filter(student__identifier__in=student, id=query).order_by(sortname)[offset:limited]
            else:
                results = Donation.objects.filter(student__identifier__in=student).order_by(sortname)[offset:limited]
        except Exception, e:
            pass
        return results

    def get_donations_total(self, student, query=None, field='id'):
        try:
            if query:
                if field == 'last_name':
                    return Donation.objects.filter(student__identifier__in=student, last_name__contains=query).count()
                elif field == 'first_name':
                    return Donation.objects.filter(student__identifier__in=student, first_name__contains=query).count()
                elif field == 'email_address':
                    return Donation.objects.filter(student__identifier__in=student, email_address__contains=query).count()
                elif field == 'phone_number':
                    return Donation.objects.filter(student__identifier__in=student, phone_number__contains=query).count()
                else:
                    return Donation.objects.filter(student__identifier__in=student, id=query).count()
            else:
                return Donation.objects.filter(student__identifier__in=student).count()
        except:
            return 0

    def get_total(self, ids=None):
        try:
            donation = Donation.objects.filter(id__in=ids).aggregate(total=Sum('donated'))
            return CurrencyField().to_python(donation['total'])
        except Exception, e:
            return 0

    def reports_totals_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            json['values'][index]['values'].append(grade.total_collected())
            json['values'][index]['labels'].append('Laps: {0}; Donations'.format(grade.total_laps()))
        return json

    def reports_most_laps_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            laps = { }
            for teacher in teachers:
                num_laps = Student.objects.filter(teacher=teacher, laps__gt=0).exclude(disqualify=True).aggregate(num_laps=Sum('laps'))
                laps[teacher.full_name()] = num_laps['num_laps'] or 0
            for key, value in sorted(laps.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_laps_by_grade_avg(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            laps = { }
            for teacher in teachers:
                results  = Student.objects.filter(teacher=teacher, laps__gt=0).exclude(disqualify=True).aggregate(num_laps=Sum('laps'))
                students = teacher.total_students(1)
                avg_laps = 0
                if results['num_laps'] and students:
                    avg_laps = float(results['num_laps']) / students
                laps[teacher.full_name()] = round(avg_laps, 2)
            for key, value in sorted(laps.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_laps_by_student_by_grade(self, gender=None):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            if gender:
                students = Student.objects.filter(teacher__grade=grade, gender=gender, laps__gt=0).exclude(disqualify=True).annotate(max_laps=Max('laps')).order_by('-laps')[:20]
            else:
                students = Student.objects.filter(teacher__grade=grade, laps__gt=0).exclude(disqualify=True).annotate(max_laps=Max('laps')).order_by('-laps')[:20]
            for student in students:
                json['values'][index]['values'].append(student.max_laps or 0)
                json['values'][index]['labels'].append(student.full_name())
        return json

    def reports_most_donations_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            totals = { }
            for teacher in teachers:
                results = Student.objects.filter(teacher=teacher).aggregate(total_collected=Sum('collected'))
                totals[teacher.full_name()] = float(results['total_collected'] or 0)
            for key, value in sorted(totals.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_donations_by_grade_avg(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            teachers = Teacher.objects.filter(grade=grade).exclude(list_type=3).all()
            totals = { }
            for teacher in teachers:
                results = Student.objects.filter(teacher=teacher).aggregate(total_collected=Sum('collected'))
                students = teacher.total_students()
                total_collected = 0
                if results['total_collected'] and students:
                    total_collected = results['total_collected'] / students
                totals[teacher.full_name()] = round(total_collected, 2)
            for key, value in sorted(totals.iteritems(), key=lambda (v,k): (k,v), reverse=True):
                json['values'][index]['values'].append(value)
                json['values'][index]['labels'].append(key)
        return json

    def reports_most_donations_by_day_by_sponsor(self):
        json = {'label': [], 'values': []}
        now = date.datetime.now(pytz.utc)
        for index in range(1, 11):
            end = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index-1)
            start = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index)
            json['values'].append({'label': end.strftime('%m/%d/%Y'), 'values': [], 'labels': []})
            results = Donation.objects.filter(date_added__range=(start, end)).exclude(type__in=[1,2]).order_by('-donated')
            for result in results:
                json['values'][index-1]['values'].append(float(result.donated or 0))
                json['values'][index-1]['labels'].append('<span id="{0}">{1} ({2})</span>'.format(result.id, result.full_name(), result.student))
        return json

    def reports_most_donations_by_day(self):
        json = {'label': [], 'values': []}
        donated = Donation.objects.aggregate(donated=Sum('donated'))
        collected = Student.objects.aggregate(collected=Sum('collected'))
        json['values'].append({'label': 'Pledged', 'values': [float(donated['donated'] or 0)], 'labels': ['Total Pledged']})
        json['values'].append({'label': 'Collected', 'values': [float(collected['collected'] or 0)], 'labels': ['Total Collected']})
        now = date.datetime.now(pytz.utc)
        for index in range(2, 12):
            end = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index-1)
            start = date.datetime(now.year, now.month, now.day, 23, 59, 59, 0, pytz.utc) - date.timedelta(index)
            json['values'].append({'label': end.strftime('%m/%d/%Y'), 'values': [], 'labels': []})
            results = Donation.objects.filter(date_added__range=(start, end)).aggregate(donated=Sum('donated'))
            json['values'][index]['values'].append(float(results['donated'] or 0))
            json['values'][index]['labels'].append(start.strftime('%m/%d/%Y'))
        return json

    def reports_most_donations_by_student_by_grade(self):
        json = {'label': [], 'values': []}
        grades = Grade.objects.all()
        for index, grade in enumerate(grades):
            json['values'].append({'label': grade.title, 'values': [], 'labels': []})
            students = Student.objects.filter(teacher__grade=grade).annotate(max_funds=Max('collected')).order_by('-collected')[:20]
            for student in students:
                json['values'][index]['values'].append(float(student.collected or 0))
                json['values'][index]['labels'].append(student.full_name())
        return json

    def reports_most_donations_by_student(self):
        json = {'label': [], 'values': []}
        students = Student.objects.annotate(max_funds=Max('collected')).order_by('-collected')[:20]
        for student in students:
            json['values'].append({'label': student.id, 'values': [float(student.max_funds or 0)], 'labels': [student.full_name()]})
        return json

    def reports_most_donations_by_student_pledged(self):
        json = {'label': [], 'values': []}
        students = Student.objects.annotate(max_funds=Max('pledged')).order_by('-pledged')[:20]
        for student in students:
            json['values'].append({'label': student.id, 'values': [float(student.max_funds or 0)], 'labels': [student.full_name()]})
        return json

    def reports_donations_by_teacher(self, id=0):
        json = {'label': [], 'values': []}
        if id == 0:
            donation = Donation.objects.filter(type=2).aggregate(donated=Sum('donated'))
            if donation:
                json['values'].append({'label': 0, 'values': [float(donation['donated'] or 0)], 'labels': ['Mrs. Agopian']})
            teachers = Teacher.objects.exclude(list_type=3).all()
            for index, teacher in enumerate(teachers):
                donation = teacher.get_donations()
                if donation:
                    json['values'].append({'label': teacher.id, 'values': [donation], 'labels': [teacher.full_name()]})
        else:
            teacher  = Teacher.objects.filter(id=id).get()
            students = Student.objects.filter(teacher=teacher).all()
            json['values'].append({'label': 'Donations', 'values': [], 'labels': []})
            for student in students:
                donation = student.total_sum()
                if donation['total_sum']:
                    json['values'][0]['values'].append(float(donation['total_sum'] or 0))
                    json['values'][0]['labels'].append(student.full_name())
            donations = Donation.objects.filter(first_name__contains=teacher.last_name).order_by('-donated')
            json['values'].append({'label': 'Sponsors', 'values': [], 'labels': []})
            totals = { }
            for index, donation in enumerate(donations):
                full_name = donation.student.full_name()
                if totals.has_key(full_name):
                    totals[full_name] += donation.donated or 0
                else:
                    totals[full_name] = donation.donated or 0
            for student, total in totals.iteritems():
                json['values'][1]['values'].append(float(total or 0))
                json['values'][1]['labels'].append(student)
        return json

    def reports_unpaid_donations(self):
        data = []
        total_donated = 0
        donations = Donation.objects.exclude(paid=1).order_by('student__teacher__last_name', 'student__last_name', 'student__first_name')
        for index, donation in enumerate(donations):
            total_donated += donation.total() or 0
            data.append({'id': index+1, 'date': donation.date_added, 'teacher': donation.student.teacher, 'student': donation.student, 'name': donation.full_name(), 'donation': donation.donation or 0, 'type': donation.per_lap and 'Per Lap' or 'Flat', 'total': donation.total() or 0, 'paid': donation.paid and 'Yes' or 'No'})
        data.append({'id': '&nbsp;', 'date': 'Total', 'student': '&nbsp;', 'teacher': '&nbsp;', 'name': '&nbsp;', 'donation': None, 'total': total_donated, 'paid': '&nbsp;'})
        return data

    def verify_paypal_donations(self, grade=None):
        data = []
        count = 0
        total_paid = 0
        total_donated = 0
        cwd = os.path.dirname(os.path.realpath(__file__))
        PAYPAL_CSV_REPORT = os.path.join(cwd, settings.PAYPAL_CSV_REPORT)
        with open(PAYPAL_CSV_REPORT, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            fields = []
            for index, row in enumerate(csv_reader):
                if index == 0:
                    for r in row: fields.append(r.strip())
                    continue
                row = dict(zip(fields, row))
                ids = row['Item ID'].split('-')[-1]
                if regex.match('[0-9.,]+', ids):
                    total_paid += float(row['Gross'])
                    gross = row['Gross']
                    for id in ids.split(','):
                        count += 1
                        try:
                            donation = Donation.objects.filter(id=id).get()
                            if not grade or donation.student.teacher.grade.title == grade:
                                total_donated += donation.donated or 0
                                data.append({'id': count, 'date': row['Date'], 'student': donation.student, 'teacher': donation.student.teacher, 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': gross, 'donation': donation.donated or 0, 'paid': donation.paid and 'Yes' or 'No'})
                        except:
                            data.append({'id': count, 'date': row['Date'], 'student': 'N/A', 'teacher': 'N/A', 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': gross, 'donation': 'N/A', 'paid': 'N/A'})
                        gross = ''
                else:
                    count += 1
                    try:
                        names = row['Name'].split()
                        donation = Donation.objects.filter(first_name=names[0], last_name=names[1]).get()
                        if not grade or donation.student.teacher.grade.title == grade:
                            total_donated += donation.donated or 0
                            data.append({'id': count, 'date': row['Date'], 'student': donation.student, 'teacher': donation.student.teacher, 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': row['Gross'], 'donation': donation.donated or 0, 'paid': donation.paid and 'Yes' or 'No'})
                    except:
                        data.append({'id': count, 'date': row['Date'], 'student': 'N/A', 'teacher': 'N/A', 'name': row['Name'], 'emnail': row['From Email Address'], 'item': row['Item ID'], 'gross': row['Gross'], 'donation': 'N/A', 'paid': 'N/A'})
        data.append({'id': '&nbsp;', 'date': 'Total', 'student': '&nbsp;', 'teacher': '&nbsp;', 'name': '&nbsp;', 'emnail': '&nbsp;', 'item': '&nbsp;', 'gross': total_paid, 'donation': total_donated, 'paid': '&nbsp;'})
        return data

    def calculate_totals(self, id=None):
        if id:
            donation = (self.id == id) and self or Donation.objects.get(pk=id)
            donation.donated = donation.total() or 0
            donation.save()
        else:
            donations = Donation.objects.all()
            for donation in donations:
                donation.donated = donation.total() or 0
                donation.save()

    def thank_you_url(self):
        site = Site.objects.get_current()
        return 'http://{0}/thank-you'.format(site.domain)

    def payment_url(self, ids=None):
        url = self.student.payment_url()
        if ids:
            return '{0}/{1}'.format(url, ids)
        else:
            return '{0}?sponsor={1}'.format(url, self.email_address)

    def button_data(self, amount=None, ids=None):
        if not amount: amount = self.total() or 0
        if not ids: ids = self.id
        site = Site.objects.get_current()
        now = date.datetime.now(pytz.utc)
        data = {
            'rm': 1,
            'lc': 'US',
            'no_note': 0,
            'no_shipping': 2,
            'cmd': '_donations',
            'currency_code': 'USD',
            'business': settings.PAYPAL_BUS_ID,
            'item_number': 'husky-hustle-donation-{0}'.format(ids),
            'item_name': 'Husky Hustle Online Donations {0}'.format(now.year),
            'return': 'http://{0}/thank-you'.format(site.domain),
            'notify_url': 'http://{0}/paid/{1}'.format(site.domain, ids),
            'cert_id': settings.PAYPAL_CERT_ID,
            'amount': amount,
        }
        return data

    def encrypted_block(self, data=None):
        if not data: data = self.button_data()
        paypal = PayPal()
        return paypal.encrypt(data)


class Pledge(models.Model):

    email_address = models.CharField(max_length=100, blank=False, null=False, default='_sponsor_@huskyhustle.com')
    donation = models.ForeignKey(Donation, related_name='pledges')

    def get_donations(self, email_address=None):
        if not email_address: return
        return Pledge.objects.filter(email_address=email_address)


# Generating public/private keys
# openssl genrsa -out private_key.pem 1024
# openssl req -new -key private_key.pem -x509 -days 365 -out public_key.pem
class PaymentGateway(models.Model):

    gateway = models.CharField(max_length=100, blank=False, null=False, default=None)
    api_key = models.CharField(max_length=250, blank=True, null=True, default=None)
    api_secret = models.CharField(max_length=250, blank=True, null=True, default=None)
    client_id = models.CharField(max_length=250, blank=True, null=True, default=None)
    business_id = models.CharField(max_length=250, blank=True, null=True, default=None)
    public_cert = models.TextField(max_length=65000, blank=True, null=True, default=None)
    public_key = models.TextField(max_length=65000, blank=True, null=True, default=None)
    private_key = models.TextField(max_length=65000, blank=True, null=True, default=None)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def decode_business_id(self):
        return base64.b64decode(self.business_id)

    @property
    def decode_business_id(self):
        return base64.b64decode(self.business_id)

    def save(self, *args, **kwargs):
#         if self.client_id:
#             self.client_id = base64.b64encode(self.client_id)
#         if self.business_id:
#             self.business_id = base64.b64encode(self.business_id)
        return super(PaymentGateway, self).save(*args, **kwargs)


class Shirt(models.Model):

    TYPES = (
        (1, 'Child'),
        (2, 'Adult'),
    )
    SIZES = (
        (1, 'XS (2-4)'),
        (2, 'S (6-8)'),
        (3, 'M (10-12)'),
        (4, 'L (14-16)'),
        (5, 'XL (Adult Small)'),
        (6, 'S'),
        (7, 'M'),
        (8, 'L'),
        (9, 'XL'),
        (10, 'XXL'),
    )
    type = models.IntegerField(blank=True, null=True, choices=TYPES)
    size = models.IntegerField(blank=True, null=True, choices=SIZES)
    price = CurrencyField(blank=True, null=True, default=10.00)

    def __unicode__(self):
        return self.full_name()

    def full_name(self):
        return '{0} {1}'.format(self.type_display(), self.size_display())

    def type_display(self):
        d = dict(self.TYPES)
        if self.type in d:
            return d[self.type]

    def size_display(self):
        d = dict(self.SIZES)
        if self.size in d:
            return d[self.size]


class ShirtOrder(models.Model):

    email_address = models.CharField(max_length=100, default='_sponsor_@huskyhustle.com')
    student = models.ForeignKey(Student, related_name='orders')
    shirt = models.ForeignKey(Shirt, related_name='shirtorders')
    quantity = models.IntegerField(blank=True, null=True)
    price = CurrencyField(blank=True, null=True)
    paid = models.BooleanField(null=False, default=0)
    paid_by = models.CharField(max_length=6, blank=True, null=True, default='online', choices=(('cash','cash'), ('check','check'), ('online','online')))
    date_added = models.DateTimeField(auto_now_add=True)


class ShirtOrderForm(forms.Form):

    email_address = models.CharField(max_length=100)

class DonationForm(forms.Form):

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email_address = forms.EmailField(max_length=100)
    donation = CurrencyField(max_digits=100)

    def clean(self):
        if 'donation' in self.cleaned_data:
            value  = self.cleaned_data['donation']
            result = Decimal(value)
            if not result:
                raise forms.ValidationError("Donation needs to be a Currency value")
            return value

        if 'phone_number' in self.cleaned_data:
            value = self.cleaned_data['phone_number']
            phoneMatchRegex = regex.compile(r"^[0-9\-\(\) \.]*$")
            phoneSplitRegex = regex.compile(r"[\-\(\) \.]")
            if not value:
                raise forms.ValidationError("Phone number is required")
            if not phoneMatchRegex.match(value):
                raise forms.ValidationError("Phone number can only have dashes, parenthesis, spaces, dots and numbers in them")
            phone = "".join(phoneSplitRegex.split(value))
            if len(phone) > 10:
                raise forms.ValidationError("Phone number can only be 10 digits long")


class ContactForm(forms.Form):

    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)


# post save signals
# post_save.connect(calculate_totals_callback, sender=Student, dispatch_uid="calculate_student_totals_callback")
# post_save.connect(calculate_totals_callback, sender=Donation, dispatch_uid="calculate_donation_totals_callback")
