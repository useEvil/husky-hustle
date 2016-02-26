import os, csv, sys, pytz, argparse

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
    teachers = dict()
    students = dict()
    save = False

#     parser = argparse.ArgumentParser(description='Process some integers.')
#     parser.add_argument('file_path', metavar='N', type=str, nargs='+', help='A CSV file to parse')
#     parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')
    option_list = BaseCommand.option_list + (
        make_option('--all', action='store_true', dest='all', default=False, help='All'),
        make_option('--save', action='store_true', dest='save', default=False, help='Save all Student Data'),
        make_option('--teacher', action='store_true', dest='teacher', default=False, help='Process Teachers'),
        make_option('--student', action='store_true', dest='student', default=False, help='Process Students'),
    )

    def handle(self, *args, **options):

        for key in ['all', 'save', 'teacher', 'student']:
            setattr(self, key, options.get(key, None))

        try:
            count = 0
            for filename in args:
                with open(filename, 'r') as csv_file:
                    reader = csv.DictReader(csv_file)
                    for row in reader:
                        print '==== row [{0}]'.format(row)
                        teacher = self.process_teachers(row)
                        student = self.process_students(row, teacher)
                        count += 1
                        self.stdout.write('Successfully Imported Student: {0} == {1}'.format(teacher, student))

            self.stdout.write('Successfully Imported {0} Students from "{1}"'.format(count, filename))
        except Exception, e:
            raise CommandError('Could not parse file "{0}"'.format(e))

    def process_teachers(self, row):
        if not self.teacher and not self.student: return
        teacher_name = regex.sub(r'\d+', '', row.get('teacher').strip())
        grade = Grade.objects.get(grade=int(row.get('grade', '0').strip()))
        room = row.get('room').strip()
        room_grade = "{0}-{1}".format(room, grade)
        if room_grade in self.teachers:
            return self.teachers[room_grade]
        try:
            teacher = Teacher.objects.get(grade=grade, room_number=room, list_type__in=[1,2])
        except ObjectDoesNotExist as err:
            print '==== teacher.room.exist.err [{0}][{1}]'.format(teacher_name, err)
            try:
                teacher = Teacher.objects.get(grade=grade, last_name=teacher_name)
            except:
                print '==== teacher.name.exist.err [{0}][{1}]'.format(teacher_name, err)
                teacher = Teacher(grade=grade)
            finally:
                teacher.list_type = 2 if teacher_name.find('/') else 1
                teacher.room_number = room
                teacher.last_name = teacher_name
                teacher.email_address = 'teacher@tustin.k12.ca.us'
                teacher.website = 'http://tusd.haikulearning.com/'
                print '==== teacher [{0}]'.format(teacher)
                if self.save:
                    try:
                        teacher.save()
                    except Exception as err:
                        print '==== teacher.save.err [{0}]'.format(err)
                print '==== teacher.save [{0}]'.format(teacher)
        self.teachers[room_grade] = teacher
        return teacher

    def process_students(self, row, teacher):
        if not self.student: return
        first_name = row.get('first_name').strip()
        last_name = row.get('last_name').strip()
        gender = row.get('gender', 'F').strip()
        full_name = "{0}, {1}".format(last_name, first_name)
        if full_name in self.students:
            return self.students[full_name]
        try:
            student = Student.objects.get(first_name=first_name, last_name=last_name, teacher=teacher)
        except ObjectDoesNotExist as err:
            student = Student(
                first_name=first_name,
                last_name=last_name,
                teacher=teacher
            )
        finally:
            student.identifier = student.get_identifier
            student.gender = gender
            if self.save:
                try:
                    student.save()
                except Exception as err:
                    print '==== student.save.err [{0}]'.format(err)
            print '==== student.save [{0}]'.format(student)
        self.students[full_name] = student
        return student

    def process_all(self, row):
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

    def create_teacher(self, teacher, span):
        if teacher:
            print '==== Total Added [{0}]'.format(teacher.students.count())
        print '==== Finding Teacher [{0}]'.format(span.string)
        teacher = Teacher.objects.get(last_name=span.string)
        print '==== teacher [{0}]'.format(teacher)
        return teacher
