from login import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import generate_token
from django.core.mail import EmailMessage, send_mail
from django.contrib.sites.shortcuts import get_current_site

def home(request):
    return render(request, "authentication/index.html")

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if pass1 != pass2:
            messages.error(request, "Passwords do not match!")
            return redirect('home')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('home')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be alphanumeric!")
            return redirect('home')
        
        if len(username)>10:
            messages.error(request, "Username must be less than 10 characters!")
            return redirect('home')
            
        myuser = User.objects.create_user(username=username, email=email, password=pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()
        messages.success(request, "Your account has been successfully created.Please confirm your email to activate your account")
        
        #Welcome email
        subject = "Welcome to AUTH"
        message = " Hello " + myuser.first_name +"!! \n Thank you for visiting our site,a confirmation email has also been sent to you. \n Kindly confirm your email address. \n\n Thank you!" 
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
        #Confirmation email
        current_site = get_current_site(request)
        email_subject = "Confirm your email address"
        message2 = render_to_string('confirm_email.html',{
            'name' : myuser.first_name,
            'domain' : current_site.domain,
            'uid' : urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token' : generate_token.make_token(myuser)
        })
        
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()
        
   
        return redirect('signin')

    return render(request, "authentication/signup.html")

def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username=username, password=pass1)  # ✅ Fixed authentication issue

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}! You've successfully logged in.")
            return redirect('home')  # Redirect to avoid resubmitting form

        else:
            messages.error(request, "× Bad Credentials")
            return redirect('signin')

    return render(request, "authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('home')


def activate(request, uidb64,token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None
        
    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login (request, myuser)
        return redirect('home')
    else:
        return render(request, 'activation_fail.html')
    
