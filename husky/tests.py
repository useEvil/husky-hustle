from django.test import TestCase

from husky.models import Student, Pledge, Donation, Teacher, Grade, Album, Photo, Content, Blog, Message, Link, Calendar, Shirt, ShirtOrder
from husky.helpers import *

# Create your tests here.
class StudentTestCase(TestCase):

    def setUp(self):
        self.student = None
        self.teacher = Teacher.objects.get(pk=28)
        self.grade = Grade.objects.get(pk=5)

    def test_student_one(self):
        self.student = Student.objects.get(pk=2868)

        ## check if instance matches
        self.failUnlessEqual(isinstance(self.student, Student), True)

        ## check if identifier matches
        self.assertEqual(self.student.identifier, self.student.get_identifier)
        self.assertEqual(self.student.identifier, 'brooke-nguyen-635')
        self.assertEqual(self.student.get_identifier, 'brooke-nguyen-635')

    def test_student_two(self):
        self.student = Student.objects.get(pk=2866)

        ## check if instance matches
        self.failUnlessEqual(isinstance(self.student, Student), True)

        ## check identifier
        self.assertEqual(self.student.identifier, self.student.get_identifier)
        self.assertEqual(self.student.identifier, 'syna-mirsoltani-fallahi-635')
        self.assertEqual(self.student.get_identifier, 'syna-mirsoltani-fallahi-635')

    def test_student_three(self):
        self.student = Student(
            first_name='Brooke-Thi',
            last_name='Nguyen',
            gender='F',
            teacher=self.teacher
        )

        ## check if instance matches
        self.failUnlessEqual(isinstance(self.student, Student), True)

        ## check if identifier matches
        self.assertEqual(self.student.get_identifier, 'brooke-thi-nguyen-635')

        ## check if identifier matches
        self.student.first_name = 'Brooke Jr.'
        self.assertEqual(self.student.get_identifier, 'brooke-jr-nguyen-635')

    def test_teacher(self):
        ## check if instance matches
        self.failUnlessEqual(isinstance(self.teacher, Teacher), True)

        ## check if info matches
        self.assertEqual(self.teacher.last_name, 'Bailey')
        self.assertEqual(self.teacher.room_number, '635')
        self.assertEqual(self.teacher.grade, self.grade)
