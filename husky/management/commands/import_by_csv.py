import os, csv, sys, pytz

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
            setattr(self, key, options.get(key, None))

        try:
            count = 0
            for filename in args:
                with open(filename, 'r') as csv_file:
                    reader = csv.DictReader(csv_file)
                    for row in reader:
                        teacher_name = regex.sub(r'\d+', '', row['teacher'])
                        grade = int(row['grade']) - 1
                        try:
                            teacher = Teacher.objects.get(last_name=teacher_name)
                        except Exception as e:
                            print '==== e [{0}][{1}]'.format(teacher_name, e)
                            continue
                        try:
                            student = Student.objects.get(first_name=row['first_name'], last_name=row['last_name'], teacher__grade__grade=grade)
                        except Exception as e:
                            student = Student(
                                first_name=row['first_name'],
                                last_name=row['last_name'],
                                teacher=teacher
                            )
                            student.identifier = student.get_identifier
                            student.save()
#                             print '==== student.create [{0}]'.format(student)
                        else:
                            student.teacher = teacher
                            student.identifier = student.get_identifier
                            student.save()
#                             print '==== student.save [{0}]'.format(student)
                        count += 1


            self.stdout.write('Successfully Imported {0} Students from "{1}"'.format(count, filename))
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
