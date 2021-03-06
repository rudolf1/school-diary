from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from .models import *
from .forms import *
from .decorators import unauthenticated_user, admin_only, allowed_users
from .models import *


@unauthenticated_user
def user_register(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Учётная запись была создана успешно.")
            return redirect('/login')
    if request.POST:
        form = StudentSignUpForm(request.POST)
    else:
        form = StudentSignUpForm()
    return render(request, 'registration.html', {'form': form, 'error': 0})


@unauthenticated_user
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        print(user)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect("/")
        else:
            messages.info(request, 'Неправильный адрес электронной почты или пароль.')
    form = UsersLogin()
    context = {'form': form}
    return render(request, 'login.html', context)


def user_logout(request):
    logout(request)
    return redirect('/login/')


@login_required(login_url="/login/")
def user_profile(request):
    if request.user.account_type == 0:
        data = Users.objects.get(email=request.user)
    if request.user.account_type == 1:
        data = Administrators.objects.get(account=request.user)
    if request.user.account_type == 2:
        data = Teachers.objects.get(account=request.user)
    if request.user.account_type == 3:
        data = Students.objects.get(account=request.user)
    context = {'data':data}
    return render(request, 'profile.html', context)


@login_required(login_url="/login/")
@admin_only
def admin_register(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Новый администратор был создан успешно.")
            return redirect('/login/')
    if request.POST:
        form = AdminSignUpForm(request.POST)
    else:
        form = AdminSignUpForm()
    return render(request, 'registration_admin.html', {'form': form, 'error': 0})


@login_required(login_url="/login/")
@admin_only
def teacher_register(request):
    if request.method == 'POST':
        form = TeacherSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Новый учитель был создан успешно.")
            return redirect('/login/')
    if request.POST:
        form = TeacherSignUpForm(request.POST)
    else:
        form = TeacherSignUpForm()
    return render(request, 'registration_teacher.html', {'form': form, 'error': 0})


def create_table(lessons, students):
    scope = {}
    for student in students:
        stu = {}
        for lesson in lessons:
            try:
                stu.update({lesson: student.marks_set.get(lesson=lesson)})
            except ObjectDoesNotExist:
                stu.update({lesson: None})
        scope.update({student: stu})
    return scope


def create_table_of_results(subjects, student, grade):
    table = {}
    for subject in subjects:
        s = {}
        lessons = Lessons.objects.filter(subject=subject, grade=grade)
        for lesson in lessons:
            s.update({lesson: Marks.objects.get(lesson=lesson, student=student)})
        table.update({subject: s})
    return table


@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
@login_required(login_url="/login/")  # TODO fix bug
def lesson_page(request):
    pk = request.GET.get('pk')
    lesson = Lessons.objects.get(pk=pk)
    if request.method == 'POST':
        form = LessonEditForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
        else:
            print('Not Valid, dude')
    form = LessonEditForm(instance=lesson)
    context = {
        'lesson': lesson,
        'form':form
        }
    return render(request, 'lesson_page.html', context)


def get_averange(list):
    """
    In: list of marks (integers)
    Out: averange value
    """
    return round(sum(list) / len(list), 2)


@login_required(login_url="/login/")
def diary(request):
    """
    Main function for displaying diary pages to admins/teachers/students.
    """

    # If user is admin
    if request.user.account_type == 0 or request.user.account_type == 1:
        return render(request, 'diary_admin_main.html')

    # If user is student
    elif request.user.account_type == 3:
        student = Students.objects.get(account=request.user)
        grade = student.grade
        if request.method == "POST":
            subject = request.POST['subject']
            term = request.POST['term']
            subject = Subjects.objects.get(id=subject)
            lessons = Lessons.objects.filter(grade=grade, subject=subject)
            marks = []
            for i in lessons:
                try: marks.append(Marks.objects.get(student=student, lesson=i))
                except: pass

            # If student has no marks than send him a page with info.
            # Otherwise, student will get a page with statistics and his results.
            if marks:
                n_amount = 0
                marks_list = []
                for i in marks:
                    m = i.amount
                    if m == -1:
                        n_amount += 1
                    else:
                        marks_list.append(m)
                avg = get_averange(marks_list) # Get averange of marks
                data = []
                for i in range(5, 1, -1): data.append(marks_list.count(i))
                data.append(n_amount)
                context = {
                    'lessons':lessons, 
                    'marks':marks,
                    'subject':subject,
                    'data':data,
                    'avg':avg,
                    'term':term}
                return render(request, 'results.html', context)
            return render(request, 'no_marks.html')
        subjects = grade.subjects.all()
        context = {'subjects':subjects}
        return render(request, 'diary_student.html', context)

    # If user is teacher
    elif request.user.account_type == 2:
        teacher = Teachers.objects.get(account=request.user)
        controls = Controls.objects.all()
        context = {'Teacher': teacher,
                   'subjects': teacher.subjects.all(),
                   'grades': Grades.objects.filter(teachers=teacher),
                   'controls':controls
                   }

        if request.method == 'POST':
            # If teacher filled in a form with name = 'getgrade' then
            # build a table with marks for all students and render it.
            if 'getgrade' in request.POST:
                subject = Subjects.objects.get(name=request.POST.get('subject'))
                grade = request.POST.get('grade')
                request.session['subject'] = subject.id
                if len(grade) == 3: number = int(grade[0:2])
                else: number = int(grade[0])
                letter = grade[-1]
                try:
                    grade = Grades.objects.get(number=number, subjects=subject, letter=letter, teachers=teacher)
                    request.session['grade'] = grade.id
                except ObjectDoesNotExist:
                    messages.error(request, 'Ошибка')
                    return render(request, 'teacher.html', context)
                lessons = Lessons.objects.filter(grade=grade, subject=subject)
                students = Students.objects.filter(grade=grade)
                scope = create_table(lessons, students) # Create a table
                context.update({
                    'is_post': True,
                    'lessons': lessons,
                    'scope': scope
                })
                return render(request, 'teacher.html', context)

            elif 'createlesson' in request.POST:
                date = request.POST.get('date')
                theme = request.POST.get('theme')
                homework = request.POST.get('homework')
                control = Controls.objects.get(id=request.POST.get('control'))
                grade = Grades.objects.get(id=request.session['grade'])
                subject = Subjects.objects.get(id=request.session['subject'])
                lesson = Lessons.objects.create(
                    date=date, theme=theme, homework=homework, control=control, grade=grade, subject=subject
                )
                lesson.save()
                return HttpResponseRedirect('/')

            # GETTING MARKS FROM FORM AND SAVE THEM
            # TODO: Optimize this algorithm, because it's slow
            else:
                # We make a dictionary from all data we send
                for i in dict(request.POST):
                    # Missing a csrf token
                    if i == 'csrfmiddlewaretoken':
                        continue
                    
                    # Split them. We get a student (li[0]) and id of
                    # lesson (li[1])
                    li = i.split('|')
                    account = li[0]
                    id_les = li[1]
                    
                    # Get a student by his/her email
                    student = Students.objects.get(account=Users.objects.get(email=account))
                    
                    # Get a lesson by it's id
                    lesson = Lessons.objects.get(pk=id_les)
                    amount = str(request.POST[i])
                    
                    # If we can get a mark then change it, otherwise create a new one
                    try:
                        mark = Marks.objects.get(lesson=lesson, student=student)
                        if amount:
                            mark.amount = amount
                            mark.save()
                        else:
                            mark.delete()
                    except ObjectDoesNotExist:
                        if amount:
                            Marks.objects.create(lesson=lesson,
                                                 student=student,
                                                 amount=amount
                                                 )
                return redirect(diary)
        else:
            return render(request, 'teacher.html', context)
    else:
        redirect('/')


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def add_student_page(request):
    """
    Page where teachers can add students to their grade.
    """
    try:
        grade = Grades.objects.get(main_teacher=request.user.id)
    except ObjectDoesNotExist:
        return render(request, 'access_denied.html', {'message':"Вы не классный руководитель."})
    students = Students.objects.filter(grade=grade)

    if request.method == "POST":
        form = AddStudentToGradeForm(request.POST)
        if form.is_valid:
            fn = request.POST.get('first_name')
            s = request.POST.get('surname')
            search = Students.objects.filter(first_name=fn, surname=s)
            context = {'form':form, 'search':search, 'grade':grade, 'students':students}
            return render(request, 'grades/add_student.html', context)
    
    form = AddStudentToGradeForm()
    context = {'form':form, 'grade':grade, 'students':students}
    return render(request, 'grades/add_student.html', context)


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def add_student(request, i):
    """
    Function defining the process of adding new student to a grade and confirming it.
    """
    u = Users.objects.get(email=i)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        try:
            grade = Grades.objects.get(main_teacher=request.user.id)
            s.grade = grade
            s.save()
            return redirect('add_student_page')
        except ObjectDoesNotExist:
            context = {'message':"Вы не классный руководитель."}
            return render(request, 'access_denied.html', context)
    else:
        return render(request, 'grades/add_student_confirm.html', {'s':s})


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def create_grade_page(request):
    if request.method == "POST":
        form = GradeCreationForm(request.POST)
        if form.is_valid():
            grade = form.save()
            mt = Teachers.objects.get(account=request.user)
            grade.main_teacher = mt
            grade.save()
            return redirect('my_grade')
    form = GradeCreationForm()
    context = {'form':form}
    return render(request, 'grades/add_grade.html', context)


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def my_grade(request):
    """
    Page with information about teacher's grade.
    """
    me = Teachers.objects.get(account=request.user)
    try:
        grade = Grades.objects.get(main_teacher=me)
    except ObjectDoesNotExist:
        grade = None
    context = {'grade':grade}
    return render(request, 'grades/my_grade.html', context)


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def delete_student(request, i):
    """
    Function defining the process of deleting a student from a grade and confirming it.
    """
    u = Users.objects.get(email=i)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        try:
            grade = Grades.objects.get(main_teacher=request.user.id)
            s.grade = None
            s.save()
            return redirect('add_student_page')
        except ObjectDoesNotExist:
            context = {'message':"Вы не классный руководитель."}
            return render(request, 'access_denied.html', context)
    else:
        return render(request, 'grades/delete_student_confirm.html', {'s':s})


@allowed_users(allowed_roles=['teachers', 'students'], message="Вы не зарегистрированы как учитель или ученик.")
@login_required(login_url="login")
def admin_message(request):
    """
    Send a message to an admin.
    """
    if request.method == "POST":
        form = AdminMessageCreationForm(request.POST)
        if form.is_valid():
            m = form.save()
            m.sender = request.user
            m.save()
            return redirect('profile')
    form = AdminMessageCreationForm()
    return render(request, 'admin_messages.html', {'form':form})


@login_required(login_url="/login/")
@admin_only
def students_dashboard_first_page(request):
    return redirect('/students/dashboard/1')


@login_required(login_url="/login/")
@admin_only
def students_dashboard(request, page):
    """
    Send a dashboard with up to 100 students.
    TODO: Test a pagination.
    """
    students = Students.objects.all()
    students = Paginator(students, 100)
    students = students.get_page(page)
    return render(request, 'students/dashboard.html', {'students':students})


@login_required(login_url="/login/")
@admin_only
def students_delete(request, id):
    """
    Delete a student.
    """
    u = Users.objects.get(email=id)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        u.delete()
        s.delete()
        return redirect('students_dashboard')
    return render(request, 'students/delete.html', {'s':s})


@login_required(login_url="/login/")
@admin_only
def students_update(request, id):
    """
    Edit student's account info.
    """
    u = Users.objects.get(email=id)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        form = StudentEditForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            return redirect('students_dashboard')
    form = StudentEditForm(instance=s)
    return render(request, 'students/update.html', {'form':form})


@login_required(login_url="/login/")
@admin_only
def admins_dashboard_first_page(request):
    """
    Redirect user to the first page of admin dashboard.
    """
    return redirect('/admins/dashboard/1')


@login_required(login_url="/login/")
@admin_only
def admins_dashboard(request, page):
    """
    Send dashboard with up to 100 administrators
    """
    u = Administrators.objects.all()
    u = Paginator(u, 100)
    u = u.get_page(page)
    return render(request, 'admins/dashboard.html', {'users':u})


@login_required(login_url="/login/")
@admin_only
def admins_delete(request, id):
    """
    Delete an admin.
    """
    u = Users.objects.get(email=id)
    s = Administrators.objects.get(account=u)
    if request.method == "POST":
        u.delete()
        s.delete()
        return redirect('admins_dashboard')
    return render(request, 'admins/delete.html', {'s':s})


@login_required(login_url="/login/")
@admin_only
def admins_update(request, id):
    """
    Edit admin's info.
    """
    u = Users.objects.get(email=id)
    s = Administrators.objects.get(account=u)
    if request.method == "POST":
        form = AdminsEditForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            return redirect('admins_dashboard')
    form = AdminsEditForm(instance=s)
    return render(request, 'admins/update.html', {'form':form})


# TEACHERS SECTION

@login_required(login_url="/login/")
@admin_only
def teachers_dashboard_first_page(request):
    return redirect('/teachers/dashboard/1')


@login_required(login_url="/login/")
@admin_only
def teachers_dashboard(request, page):
    u = Teachers.objects.all()
    u = Paginator(u, 50)
    u = u.get_page(page)
    return render(request, 'teachers/dashboard.html', {'users':u})


@login_required(login_url="/login/")
@admin_only
def teachers_delete(request, id):
    """
    Delete a teacher.
    """
    u = Users.objects.get(email=id)
    s = Teachers.objects.get(account=u)
    if request.method == "POST":
        u.delete()
        s.delete()
        return redirect('teachers_dashboard')
    return render(request, 'teachers/delete.html', {'s':s})


@login_required(login_url="/login/")
@admin_only
def teachers_update(request, id):
    """
    Edit teachers's account info.
    """
    u = Users.objects.get(email=id)
    s = Teachers.objects.get(account=u)
    if request.method == "POST":
        form = TeacherEditForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            return redirect('teachers_dashboard')
    form = TeacherEditForm(instance=s)
    return render(request, 'teachers/update.html', {'form':form})


def homepage(request):
    """
    Return a homepage.
    """
    return render(request, 'homepage.html')


def social(request):
    """
    Return a page with link to gymnasium's social pages.
    """
    return render(request, 'social.html')


def get_help(request):
    """
    Return a page with help information.
    TODO: Change this page to documentation page: docs.html
    """
    return render(request, 'help.html')


def error404(request):
    return render(request, 'error.html', {
        'error': "404", 
        'title': "Страница не найдена.", 
        "description": "Мы не можем найти страницу, которую вы ищите."
        })


def error500(request):
    return render(request, 'error.html', {
        'error': "500", 
        'title': "Что-то пошло не так", 
        "description": "Мы работаем над этим."
        })