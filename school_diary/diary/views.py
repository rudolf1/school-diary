from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from .forms import StudentSignUpForm, StudentsLogin
from .models import Students, Subjects


def user_register(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Учётная запись была создана успешно.")
            return redirect('/diary/login')
    if request.POST:
        form = StudentSignUpForm(request.POST)
    else:
        form = StudentSignUpForm()
    return render(request, 'registration.html', {'form': form, 'error': 0})


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
    form = StudentsLogin()
    context = {'form': form}
    return render(request, 'login.html', context)


def user_logout(request):
    logout(request)
    return redirect('/diary/login/')


def user_profile(request):
    context = {}
    return render(request, 'profile.html', {})

def diary(request):
    if request.user.account_type == 3:
        student = Students.objects.get(account=request.user)
        context = {'Student':student,
                   'subjects':Subjects.objects.all(),
                   'daylist':['09.02','10.02','11.02'],
                   'marks':student.mark_set.order_by('date')}
        #return render(request,'student_subjects_TEST.html', context)
        return render(request, 'marklist.html', context)