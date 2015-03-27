import os, csv, sys, pytz

import re as regex
import datetime as date

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings

from husky.models import Student
from husky.helpers import *

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Import Student Laps from CSV file'
    soup = None
    save = False


    option_list = BaseCommand.option_list + (
        make_option('--all', action='store_true', dest='all', default=False, help='All'),
        make_option('--save', action='store_true', dest='save', default=False, help='Save all Student Laps'),
    )

    def handle(self, *args, **options):

        for key in ['all', 'save']:
            setattr(self, key, options.get(key, None))

        try:
            count = 0
            for filename in args:
                with open(filename, 'r') as csv_file:
                    reader = csv.reader(csv_file)
                    for row in reader:
                        last_name = row[0].strip()
                        first_name = row[1].strip()
                        grade = row[2].strip()
                        gender = row[3].strip() or None
                        laps = row[4].strip() or 0
                        try:
                            student = Student.objects.get(last_name=last_name, first_name=first_name, teacher__grade__grade=grade)
                        except MultipleObjectsReturned as e:
                            print '==== student.exist.e [{0}][{1}][{2}][{3}][{4}]'.format(last_name, first_name, grade, laps, e)
                        except ObjectDoesNotExist as e:
                            print '==== student.exist.e [{0}][{1}][{2}][{3}][{4}]'.format(last_name, first_name, grade, laps, e)
                            continue
                        else:
                            student.gender = gender or student.gender
                            student.laps = laps
                            if self.save:
                                try:
                                    student.save()
                                    count += 1
                                except Exception as e:
                                    print '==== student.save.e [{0}]'.format(e)
#                             print '==== student.save [{0}][{1}][{2}]'.format(student, gender, laps)

            self.stdout.write('Successfully Imported {0} Student Laps from "{1}"'.format(count, filename))
        except Exception, e:
            raise CommandError('Could not parse file "{0}"'.format(e))
