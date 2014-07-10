import os
import sys
import pytz
import re as regex
import datetime as date

from bs4 import BeautifulSoup
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings


from husky.models import Student, Grade, Teacher
from husky.helpers import *

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Import Teacher/Student Info from PDFtoHTML file'
    soup = None
    save = False


    option_list = BaseCommand.option_list + (
        make_option('--all', action='store_true', dest='all', default=False, help='All'),
        make_option('--save', action='store_true', dest='save', default=False, help='Save all Student Data'),
    )

    def handle(self, *args, **options):

        for key in ['all', 'save']:
            option = options.get(key, None)
            if option:
                setattr(self, key, option)

        for filename in args:
            try:
                soup = BeautifulSoup(open(filename))
                teacher = None
                student = None
                temp    = None
                start_student = False
                count = 0
                for div in soup.find_all('div'):
                    span_1 = div.find('span')
                    if span_1 and span_1['class'][0] not in ['cls_005', 'cls_006', 'cls_007', 'cls_008']:
                        start_student = False
                        continue
                    if span_1 and span_1['class'][0] in ['cls_007', 'cls_008']:
                        start_student = True
                    if span_1 and span_1['class'][0] == 'cls_005':
                        match = regex.compile(r'(?P<total>(\d+)) Total (?P<type>(Males|Females|Students))')
                        match_total = match.match(span_1.string)
                        if match_total:
                            print '==== Total {1} [{0}]'.format(match_total.group('total'), match_total.group('type'))

                    ## Save Teacher Information ##
                    if span_1 and not start_student:
                        span_2 = span_1.next_sibling
                        if span_2 and span_2['class'][0] == 'cls_006':
                            teacher = self.create_teacher(teacher, span_2)
                            count = 1
                            continue
                        elif span_1['class'][0] == 'cls_006':
                            temp = self.create_teacher(None, span_1)
                            temp.room_number = temp.room_number
                            temp.grade = temp.grade
                            temp.save()
                            teacher = temp
                            continue
                        elif span_1.string == 'Teacher#':
                            if teacher:
                                print '==== Total Added [{0}]'.format(teacher.students.count())
                            teacher = Teacher()
                            count = -2
                        if count == 1:
                            room = div.find('span').string
                            match = regex.compile(r'Room#\s*(?P<room>(\d+))')
                            match_room = match.match(room)
                            if match_room:
                                teacher.room_number = match_room.group('room')
                            count = 2
                        if count == 4:
                            grade_number = div.find('span')
                            grade = Grade.objects.get(grade=grade_number.string)
                            teacher.grade = grade
                            if not temp:
                                teacher.save()
                        count += 1

                    if teacher and start_student:
                        ## Save Student Information ##
                        match = regex.compile('^\d+$')
                        if match.match(span_1.string):
                            count = 1
                        if count == 2:
                            student = Student()
                            student.last_name = span_1.string
                            student.teacher = teacher
                        if count == 3:
                            student.first_name = span_1.string
                            student.identifier = '{0}-{1}-{2}'.format(replace_space(student.first_name), replace_space(student.last_name), teacher.room_number)
                        if count == 4:
                            if len(span_1.string) == 1:
                                student.gender = span_1.string
                                if self.save:
                                    student.save()
                        if count == 5:
                            student.gender = span_1.string
                            if self.save:
                                student.save()
                            print '==== student [{0}][{1}]'.format(student, student.gender)
                        count += 1
                print '==== Total Added [{0}]'.format(teacher.students.count())
                self.stdout.write('Successfully Imported Data for "{0}"'.format(filename))
            except Exception, e:
                raise CommandError('Could not parse file "{0}"'.format(e))

    def process_teachers(self):
        pass

    def process_students(self):
        pass

    def create_teacher(self, teacher, span):
        if teacher:
            print '==== Total Added [{0}]'.format(teacher.students.count())
        print '==== Finding Teacher [{0}]'.format(span.string)
        teacher = Teacher.objects.get(last_name=span.string)
        print '==== teacher [{0}]'.format(teacher)
        return teacher
