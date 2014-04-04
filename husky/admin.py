import urllib
import re as regexp

from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count, Sum, Avg, Max
from django.utils.safestring import mark_safe

from husky.models import Student, Pledge, Content, Blog, Message, Link, Donation, Grade, Teacher, Shirt, ShirtOrder


class MostLapsListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Laps View')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = ''

    def lookups(self, request, model_admin):
        return (
            ('0_laps', _('Most Laps (K)')),
            ('1_laps', _('Most Laps (1)')),
            ('2_laps', _('Most Laps (2)')),
            ('3_laps', _('Most Laps (3)')),
            ('4_laps', _('Most Laps (4)')),
            ('laps_girls', _('Most Laps by Girls')),
            ('laps_boys', _('Most Laps by Boys')),
            ('per_laps', _('Has Per Lap')),
            ('no_laps', _('Missing Laps')),
            ('outstanding', _('Outstanding')),
            ('by_teacher', _('By Teacher')),
        )
    def queryset(self, request, queryset):
        query = request.GET.get('q')
        if self.value() == '0_laps':
            return queryset.filter(teacher__grade__grade=0).order_by('-laps').all()
        elif self.value() == '1_laps':
            return queryset.filter(teacher__grade__grade=1).order_by('-laps').all()
        elif self.value() == '2_laps':
            return queryset.filter(teacher__grade__grade=2).order_by('-laps').all()
        elif self.value() == '3_laps':
            return queryset.filter(teacher__grade__grade=3).order_by('-laps').all()
        elif self.value() == '4_laps':
            return queryset.filter(teacher__grade__grade=4).order_by('-laps').all()
        elif self.value() == 'laps_girls':
            return queryset.filter(gender='F').exclude(laps=None).order_by('-laps').all()
        elif self.value() == 'laps_boys':
            return queryset.filter(gender='M').exclude(laps=None).order_by('-laps').all()
        elif self.value() == 'per_laps':
            return queryset.filter(sponsors__per_lap=True).all()
        elif self.value() == 'no_laps':
            return queryset.filter(laps=None).all()
        elif self.value() == 'outstanding':
            return queryset.filter(sponsors__paid=False).distinct().all()
        elif self.value() == 'by_teacher':
            return queryset.filter(teacher__last_name__icontains=query).all()
        else:
            return queryset.all()

class MostDonationsListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Donation Views')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = ''

    def lookups(self, request, model_admin):
        return (
            ('unpaid', _('All Unpaid')),
            ('unpaid_lap', _('Unpaid Per Lap')),
            ('unpaid_flat', _('Unpaid Flat')),
            ('perlap', _('Paid Per Lap')),
            ('flat', _('Paid Flat')),
#             ('direct', _('Direct')),
            ('online', _('Via Online')),
            ('check_cash', _('Via Cash/Check')),
            ('brooke_bree', _('Brooke+Bree')),
            ('to_teachers', _('To Teachers')),
            ('to_principal', _('To Principal')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'unpaid':
            return queryset.filter(paid=False).order_by('email_address').all()
        elif self.value() == 'unpaid_lap':
            return queryset.filter(paid=False, per_lap=True).order_by('email_address').all()
        elif self.value() == 'unpaid_flat':
            return queryset.filter(paid=False, per_lap=False).order_by('email_address').all()
        elif self.value() == 'perlap':
            return queryset.filter(paid=True, per_lap=True).all()
        elif self.value() == 'flat':
            return queryset.filter(paid=True, per_lap=False).all()
        elif self.value() == 'online':
            return queryset.filter(paid_by='online').all()
        elif self.value() == 'check_cash':
            return queryset.filter(paid_by__in=['check', 'cash']).all()
        elif self.value() == 'brooke_bree':
            return queryset.filter(student__in=[125,126]).order_by('student__last_name', 'student__first_name').all()
        elif self.value() == 'to_teachers':
            return queryset.filter(type=1).all()
        elif self.value() == 'to_principal':
            return queryset.filter(type=2).all()
        else:
            return queryset.all()

class StudentAdmin(admin.ModelAdmin):
    # override the tempalte to show results
    def get_changelist(self, request):
        return StudentList

    # create a link for the student name
    def first_name_link(obj):
        return '<a href="/admin/husky/donation/?q=%s" class="nowrap" style="font-weight: bold;font-size: 12px;">%s</a>' % (urllib.quote_plus(obj.full_name()), obj.first_name)
    first_name_link.allow_tags = True
    first_name_link.short_description = "First Name"

    fields = ['teacher', 'first_name', 'last_name', 'identifier', 'gender', 'age', 'laps', 'disqualify', 'date_added']
    list_display = ['last_name', first_name_link, 'teacher', 'identifier', 'disqualify', 'gender', 'laps', 'total_for_laps', 'total_collected', 'total_due', 'total_raffle_tickets']
    search_fields = ['teacher__last_name', 'first_name', 'last_name']
    list_editable = ['laps', 'gender', 'disqualify']
    list_filter = [MostLapsListFilter]
    save_on_top = True
    list_per_page = 40


class ContentModelForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={'cols': 125, 'rows': 50}))
    class Meta:
        model = Content

# class DonationModelForm(forms.ModelForm):
#     student = forms.IntegerField(widget=AdminStudentWidget(
#         choices=[(s.id, s.select_list_name()) for s in Student.objects.all()]
#     ), label='Student Name')
#     class Meta:
#         model = Student

class ContentAdmin(admin.ModelAdmin):
    fields = ['page', 'content', 'date_added']
    list_display = ['page', 'content', 'date_added']
    form = ContentModelForm

class BlogAdmin(admin.ModelAdmin):
    fields = ['title', 'content', 'author', 'date_added']
    list_display = ['title', 'content', 'date_added']

class MessageAdmin(admin.ModelAdmin):
    fields = ['title', 'content', 'author', 'date_added']
    list_display = ['title', 'content', 'date_added']

class StudentList(ChangeList):
    # get results and totals
    def get_results(self, *args, **kwargs):
        super(StudentList, self).get_results(*args, **kwargs)
        self.total_laps = 0
        self.total_due = 0
        self.total_collected = 0
        for student in self.result_list:
            self.total_laps += student.laps or 0
            self.total_due += student.total_due()
            self.total_collected += student.total_collected()

class DonationList(ChangeList):
    # get results and totals
    def get_results(self, *args, **kwargs):
        super(DonationList, self).get_results(*args, **kwargs)
        results1 = Donation.objects.all().aggregate(pledged=Sum('donated'))
        results2 = Donation.objects.filter(paid=True).aggregate(donated=Sum('donated'))
        self.grand_pledged = results1['pledged'] or 0
        self.grand_donated = results2['donated'] or 0
        self.total_pledged = 0
        self.total_donated = 0
        for donation in self.result_list:
            self.total_pledged += donation.total()
            if donation.paid: self.total_donated += donation.donated or 0
        self.total_due = self.total_pledged - self.total_donated

class DonationAdmin(admin.ModelAdmin):
    # create a link for the student name
    def list_name(obj):
        return '<a href="/admin/husky/student/%d/" class="nowrap">%s</a>' % (obj.student.id, obj.student.list_name())
    list_name.allow_tags = True
    list_name.short_description = "Student"

    # create a payment link for the total amount
    def total_link(obj):
        if obj.last_name == 'teacher':
            return obj.total()
        else:
            return '<a href="%s" target="_payment_url">%s</a>' % (obj.payment_url(), obj.total())
    total_link.allow_tags = True
    total_link.short_description = "Pledged"

    # override the tempalte to show results
    def get_changelist(self, request):
        return DonationList
    change_list_template = 'admin/husky/donation/change_list.html'

    def teacher_html(self):
        teachers = Teacher.objects.exclude(list_type=2).all()
        output = ['<div style="display: none;">']
        for teacher in teachers:
            output.append('<span id="%s">%s</span>' % (teacher.room_number, teacher.full_name()))
        output.append('</div>')
        return mark_safe("".join(output))

    def add_view(self, request, form_url='', extra_context=None):
        context = {}
        context.update(extra_context or {})
        context.update({'teachers': self.teacher_html()})
        return super(DonationAdmin, self).add_view(request, form_url, extra_context=context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        context = {}
        context.update(extra_context or {})
        context.update({'teachers': self.teacher_html()})
        return super(DonationAdmin, self).change_view(request, object_id, form_url, extra_context=context)

    ordering = ('-date_added',)
    fields = ['student', 'type', 'first_name', 'last_name', 'email_address', 'phone_number', 'donation', 'per_lap', 'paid', 'paid_by', 'date_added']
    list_display = ['id', list_name, 'teacher', 'first_name', 'last_name', 'email_address', 'donation', 'laps', 'per_lap', total_link, 'donated', 'date_added', 'paid', 'paid_by', 'type']
    search_fields = ['email_address', 'first_name', 'last_name', 'student__first_name', 'student__last_name', 'student__teacher__last_name', 'paid_by']
    list_editable = ['per_lap', 'donation', 'paid', 'paid_by', 'type']
    list_filter = [MostDonationsListFilter]
    save_on_top = True
    list_per_page = 50
#     form = DonationModelForm

class UserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_active']

class TeacherInline(admin.StackedInline):
    model = Teacher
    extra = 6
    verbose_name_plural = 'teachers'

class TeacherAdmin(admin.ModelAdmin):
    fields = ['grade', 'list_type', 'title', 'first_name', 'last_name', 'room_number', 'email_address', 'phone_number', 'website']
    list_display = ['grade', 'list_type', 'title', 'last_name', 'room_number', 'email_address', 'get_donations', 'total_students', 'total_participation']
    list_editable = ['list_type', 'last_name', 'room_number', 'email_address']
#     ordering = ('grade', 'last_name')

class GradeAdmin(admin.ModelAdmin):
    fields = ['grade', 'title']
    list_display = ['id', 'grade', 'title', 'total_students', 'total_laps', 'total_donations', 'total_collected', 'percent_completed', 'most_laps_avg', 'most_donations_avg']
    list_editable = ['grade', 'title']
    inlines = [TeacherInline]

class LinkAdmin(admin.ModelAdmin):
    fields = ['title', 'url', 'status']
    list_display = ['title', 'url', 'shorten', 'status']
    list_editable = ['status']

class PledgeAdmin(admin.ModelAdmin):
    def student(obj):
        return obj.donation.student
    student.allow_tags = True
    student.short_description = "Student"

    fields = ['email_address', 'donation']
    list_display = ['email_address', 'donation', student]
    search_fields = ['email_address']

class ShirtAdmin(admin.ModelAdmin):
    fields = ['type', 'size', 'price']
    list_display = ['id', 'type', 'size', 'price']

class ShirtOrderAdmin(admin.ModelAdmin):
    fields = ['student', 'shirt', 'email_address', 'quantity', 'price', 'paid', 'paid_by', 'date_added']
    list_display = ['student', 'shirt', 'email_address', 'quantity', 'price', 'paid', 'paid_by', 'date_added']

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Donation, DonationAdmin)
admin.site.register(Pledge, PledgeAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Shirt, ShirtAdmin)
admin.site.register(ShirtOrder, ShirtOrderAdmin)
