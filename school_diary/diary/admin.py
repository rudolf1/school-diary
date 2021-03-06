from django.contrib import admin
from .models import *


admin.site.site_header = "Электронный дневник"
admin.site.index_title = "Панель администратора"


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('email', 'account_type')
    list_filter = ('account_type',)


@admin.register(Students)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('account', 'first_name', 'surname', 'grade')
    list_filter = ('grade',)


@admin.register(Administrators)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('account', 'first_name', 'surname')


@admin.register(Teachers)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('account', 'first_name', 'surname')
    list_filter = ('subjects',)


admin.site.register(Grades)
admin.site.register(Marks)
admin.site.register(Lessons)
admin.site.register(AdminMessages)
admin.site.register(Controls)
admin.site.register(Subjects)

