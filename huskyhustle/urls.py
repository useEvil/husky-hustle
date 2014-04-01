from django.conf.urls import patterns, include, url
from django.contrib import admin

from husky.views import BlogFeed

admin.autodiscover()

urlpatterns = patterns('',
    # Site
    url(r'^$', 'husky.views.index', name='index'),
    url(r'^archive/album/(?P<album_id>\w+)$', 'husky.views.album', name='albums'),
    url(r'^archive/photo/(?P<album_id>\w+)/(?P<photo_id>\w+)$', 'husky.views.photo', name='photo'),
    url(r'^nav/(?P<page>\w+)/*(?P<id>\d+)*$', 'husky.views.nav', name='nav'),
    url(r'^JSON/(?P<student_id>[\w-]+)$', 'husky.views.json', name='json'),
    url(r'^paid/(?P<donation_id>[\w,-]+)$', 'husky.views.paid', name='paid'),
    url(r'^thank[-_]you/*(?P<donation_id>[\w-]+)*$', 'husky.views.thank_you', name='thank_you'),
    url(r'^emails/*$', 'husky.views.emails', name='emails'),
    url(r'^reminders/(?P<identifier>[\w-]+)$', 'husky.views.reminders', name='reminders'),
    url(r'^thanks/*$', 'husky.views.thanks', name='thanks'),
    url(r'^invite/(?P<identifier>[\w-]+)$', 'husky.views.invite', name='invite'),
    url(r'^donate/(?P<identifier>[\w-]+)$', 'husky.views.donate', name='donate'),
#     url(r'^donate[-_]direct$', 'husky.views.donate_direct', name='donate-direct'),
    url(r'^student/(?P<identifier>[\w-]*)$', 'husky.views.student', name='student'),
    url(r'^student[-_]donation/(?P<identifier>[\w-]*)$', 'husky.views.student_donation', name='student-donation'),
    url(r'^teacher[-_]donation/(?P<identifier>[\w-]*)$', 'husky.views.teacher_donation', name='teacher-donation'),
    url(r'^make[-_]payment/(?P<identifier>[\w-]+)/*(?P<id>[\d,]*)$', 'husky.views.payment', name='make-payment'),
#     url(r'^make[-_]donation/(?P<identifier>[\w-]+)/*(?P<id>[\d,]*)$', 'husky.views.make_donation', name='make-donation'),
    url(r'^donation[-_]sheet/(?P<identifier>[\w-]+)*/(?P<final>[\w-]+)*$', 'husky.views.donation_sheet', name='donation_sheet'),
    url(r'^contact/*$', 'husky.views.contact', name='contact'),
    url(r'^results/*(?P<type>[\w-]*)$', 'husky.views.results', name='results'),

    # Cart
    url(r'^add[-_]to[-_]cart/(?P<model>[\w]+)*/(?P<product_id>[\d]+)/(?P<quantity>[\d]+)*$', 'husky.views.add_to_cart', name='add_to_cart'),
    url(r'^remove[-_]from[-_]cart/(?P<product_id>[\d]+)*$', 'husky.views.remove_from_cart', name='remove_from_cart'),
    url(r'^cart/*$', 'husky.views.get_cart', name='get_cart'),
    url(r'^checkout/*$', 'husky.views.checkout_cart', name='checkout_cart'),
    url(r'^order/(?P<identifier>[\w-]*)$', 'husky.views.order_form', name='teacher-donation'),

    # rss feed
    url(r'^blog/feed$', BlogFeed()),

    # reports
    url(r'^admin/reporting/(?P<type>[\w-]+)$', 'husky.views.reporting', name='reporting'),
    url(r'^admin/reports/(?P<type>[\w-]+)$', 'husky.views.reports', name='reports'),
    url(r'^admin/results/(?P<type>[\w-]*)/*(?P<grade>[\w]*)$', 'husky.views.results', name='results'),
    url(r'^admin/(?P<type>[\w]+)/calculate_totals/*(?P<id>[\d]*)$', 'husky.views.calculate_totals', name='calculate_totals'),
    url(r'^admin/send_teacher_reports/*(?P<id>[\d,]*)$', 'husky.views.send_teacher_reports', name='send_teacher_reports'),
    url(r'^admin/send_unpaid_reports$', 'husky.views.send_unpaid_reports', name='send_unpaid_reports'),
    url(r'^admin/send_unpaid_reminders/*(?P<type>[\w]*)/*(?P<donation_id>[\d]*)/*(?P<grade>[\w]*)$', 'husky.views.send_unpaid_reminders', name='send_unpaid_reminders'),

    # Admin
    url(r'^admin/', include(admin.site.urls)),
)
