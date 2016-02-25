import os, csv, sys, pytz

import re as regex
import datetime as date

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings

from husky.models import Student, Grade, Teacher
from husky.helpers import *

class Command(BaseCommand):
    args = '<filename filename ...>'
    help = 'Import Teacher/Student Info from CSV file'
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
                        teacher_name = regex.sub(r'\d+', '', row.get('teacher'))
                        try:
                            grade = Grade.objects.get(grade=int(row.get('grade', '0')))
                        except ObjectDoesNotExist as err:
                            print '==== grade.exist.err [{0}][{1}]'.format(teacher_name, err)
                            try:
                                teacher = Teacher.objects.get(last_name=teacher_name)
                            except:
                                print '==== teacher.exist.err [{0}][{1}]'.format(teacher_name, err)

                        else:
                            try:
                                teacher = Teacher.objects.get(last_name__icontains=teacher_name, grade=grade)
                            except ObjectDoesNotExist as err:
                                print '==== teacher.exist.err [{0}][{1}][{2}]'.format(teacher_name, grade, err)
                                try:
                                    teacher = Teacher.objects.get(last_name=teacher_name)
                                except:
                                    print '==== teacher.exist.err [{0}][{1}]'.format(teacher_name, err)

                        try:
                            student = Student.objects.get(first_name=row.get('first_name'), last_name=row.get('last_name'), teacher=teacher)
                        except ObjectDoesNotExist as err:
                            student = Student(
                                first_name=row.get('first_name'),
                                last_name=row.get('last_name'),
                                gender=row.get('gender', 'F'),
                                teacher=teacher
                            )
                        finally:
                            student.identifier = student.get_identifier
                            student.gender = row.get('gender', 'F')
                            if self.save:
                                try:
                                    student.save()
                                    count += 1
                                except Exception as err:
                                    print '==== student.save.err [{0}]'.format(err)
                            print '==== student.save [{0}]'.format(student)


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
