import base64
import datetime
import json
import os

from django.contrib import messages
from django.contrib.auth import authenticate,login as auth_login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from myapp import models
from myapp.models import CyberCell, UserProfile, Post, Comment, Complaint, Notification, Like, FriendRequest, Chat, \
    GroupMember, GroupChat, Group_create, BlockedUser
from datetime import date

def home(request):
    return render(request,'index.html')


# =========  LOGIN   =======================================================

@csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            request.session['user_id'] = user.id

            if user.groups.filter(name='admin').exists():
                return redirect('adminhome')
            elif user.groups.filter(name='user').exists():
                return redirect('userhome')
            elif user.groups.filter(name='cybercell').exists():
                try:
                    cybercell = CyberCell.objects.get(USER=user)
                    request.session['cybercell_id'] = cybercell.id
                    return redirect('cyber_home')
                except CyberCell.DoesNotExist:
                    messages.error(request, 'Cybercell profile not found.')
                    return redirect('login')
            else:
                messages.error(request, 'User does not belong to a valid group.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html')




# =================================================================

@login_required(login_url='login')
@never_cache
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('login')



@login_required(login_url='login')
@never_cache
def adminhome(request):
    return render(request,'adminhome.html')




# ================ admin ===============================================
@login_required(login_url='login')
@never_cache
def admin_add_cybercell(request):
    if not request.user.groups.filter(name='admin').exists():
        messages.error(request,'Unauthorized access.')
        return  redirect('login')

    if request.method == 'POST':
        name = request.POST['name']
        username= request.POST['username']
        email= request.POST['email']
        password= request.POST['password']
        phone = request.POST['phone']
        designation = request.POST['designation']


        if User.objects.filter(username=username).exists():
            messages.error(request,'Username already exists')

        else:
            user=User.objects.create_user(
                first_name=name,
                username=username,
                email=email,
                password=password

            )
            user.save()
            try:
                group=Group.objects.get(name='cybercell')
            except Group.DoesNotExist:
                group=Group.objects.create(name='cybercell')
            user.groups.add(group)

            cybercell=CyberCell.objects.create(
                USER=user,
                phone=phone,
                designation=designation,

            )
            cybercell.save()

            messages.success(request, "Cybercell officer added successfully.")
            return redirect('admin_view_cybercell')

    return render(request,'admin_add_cybercell.html')

@login_required(login_url='login')
@never_cache
def admin_view_cybercell(request):
    cybercells = CyberCell.objects.all()
    return render(request,'admin_view_cybercell.html',{'cybercells': cybercells})

@login_required(login_url='login')
@never_cache
def admin_remove_cybercell(request, id):
    cybercell = get_object_or_404(CyberCell, id=id)
    cybercell.delete()
    messages.success(request, "Cybercell removed successfully.")
    return redirect('admin_view_cybercell')

@login_required(login_url='login')
@never_cache
def admin_view_all_users(request):
    users = UserProfile.objects.select_related('USER')
    return render(request, 'admin_view_all_users.html', {'users': users})

@login_required(login_url='login')
@never_cache
def admin_view_warned_users(request):
    users = User.objects.annotate(
        warnings_count=Count('warnings')
    ).filter(warnings_count__gt=0)

    for user in users:
        user.is_blocked = False
        if user.warnings_count >= 3:
            user.is_blocked = True
        elif user.blocked_status.first() and user.blocked_status.first().is_blocked:
            user.is_blocked = True

    return render(request, "cyber_view_warned_users.html", {
        "users": users
    })

@login_required(login_url='login')
@never_cache
def admin_view_blocked_users(request):
    users = User.objects.annotate(
        warnings_count=Count('warnings')
    )

    blocked_users = []

    for user in users:
        is_blocked = False
        if user.warnings_count >= 3:
            is_blocked = True
        elif user.blocked_status.first() and user.blocked_status.first().is_blocked:
            is_blocked = True

        if is_blocked:
            user.is_blocked = True
            blocked_users.append(user)

    return render(request, "cyber_view_blocked_users.html", {
        "users": blocked_users
    })


@login_required(login_url='login')
@never_cache
def admin_view_userprofile_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, USER=user)
    posts = Post.objects.filter(user=user)
    return render(request, 'admin_view_userprofile_detail.html', {'user': user, 'profile': profile,'posts':posts})

@login_required(login_url='login')
@never_cache
def admin_view_posts(request,user_id):
    user = get_object_or_404(User, id=user_id)
    posts = Post.objects.filter(user=user)
    return render(request, 'admin_view_posts.html', {'posts': posts,'user':user})

@login_required(login_url='login')
@never_cache
def admin_view_comments(request,post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post)
    return render(request, 'admin_view_comments.html', {'comments': comments,'post':post})


@login_required(login_url='login')
@never_cache
def admin_view_complaints(request):
    complaints=Complaint.objects.all()
    return render(request,'admin_view_complaints.html', {'complaints':complaints})


@login_required(login_url='login')
@never_cache
def admin_reply_complaints(request,complaint_id):
    complaint=get_object_or_404(Complaint,id=complaint_id)
    if request.method == 'POST':
        reply=request.POST['reply']
        complaint.reply=reply
        complaint.status = 'Updated'
        complaint.save()
        return redirect('admin_view_complaints')
    return render(request,'admin_reply_complaint.html',{'complaint':complaint})


@login_required(login_url='login')
@never_cache
def admin_add_notification(request):
    if request.method == 'POST':
        text = request.POST['text']
        Notification.objects.create(text=text)
        return redirect('admin_view_notifications')
    return render(request, 'admin_add_notification.html')


@login_required(login_url='login')
@never_cache
def admin_view_notifications(request):
    notifications = Notification.objects.all()
    return render(request, 'admin_view_notifications.html', {'notifications': notifications})
# ============ User ==========================================


# ============= CYBERCELL ===================
@login_required(login_url='login')
@never_cache
def cyber_home(request):
    cybercell_id = request.session.get('cybercell_id')
    if not cybercell_id:
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    cybercell = CyberCell.objects.get(id=cybercell_id)
    return render(request, 'cyber_home.html', {'cybercell': cybercell})



@login_required(login_url='login')
@never_cache
def cyber_view_profile(request):
    cybercell_id = request.session.get('cybercell_id')
    if not cybercell_id:
        return redirect('login')

    cybercell = CyberCell.objects.get(id=cybercell_id)
    return render(request, 'cyber_view_profile.html', {'cybercell': cybercell})


@login_required(login_url='login')
@never_cache
def cyber_view_all_users(request):
    users = UserProfile.objects.select_related('USER')
    return render(request, 'cyber_view_all_users.html', {'users': users})


def cyber_view_warned_users(request):
    users = User.objects.annotate(
        warnings_count=Count('warnings')
    ).filter(warnings_count__gt=0)

    for user in users:
        user.is_blocked = False
        if user.warnings_count >= 3:
            user.is_blocked = True
        elif user.blocked_status.first() and user.blocked_status.first().is_blocked:
            user.is_blocked = True

    return render(request, "cyber_view_warned_users.html", {
        "users": users
    })


@login_required(login_url='login')
@never_cache
def cyber_view_blocked_users(request):
    users = User.objects.annotate(
        warnings_count=Count('warnings')
    )

    blocked_users = []

    for user in users:
        is_blocked = False
        if user.warnings_count >= 3:
            is_blocked = True
        elif user.blocked_status.first() and user.blocked_status.first().is_blocked:
            is_blocked = True

        if is_blocked:
            user.is_blocked = True
            blocked_users.append(user)

    return render(request, "cyber_view_blocked_users.html", {
        "users": blocked_users
    })


@login_required(login_url='login')
@never_cache
def cyber_view_userprofile_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, USER=user)
    posts = Post.objects.filter(user=user)
    return render(request, 'cyber_view_userprofile_detail.html', {'user': user, 'profile': profile,'posts':posts})


@login_required(login_url='login')
@never_cache
def cyber_view_posts(request,user_id):
    user = get_object_or_404(User, id=user_id)
    posts = Post.objects.filter(user=user)
    return render(request, 'cyber_view_posts.html', {'posts': posts,'user':user})


@login_required(login_url='login')
@never_cache
def cyber_view_comments(request,post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post)
    return render(request, 'cyber_view_comments.html', {'comments': comments,'post':post})


# ========== user ============================


# @csrf_exempt
def register_user(request):
        first_name = request.POST['first_name']
        last_name= request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        location = request.POST['place']
        profilepic = request.POST['photos']
        gender=request.POST['gender']
        phone=request.POST['phone']
        dob=request.POST['dob']

        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists.'})
        else:
            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
            )
            user.group=Group.objects.get(name='user')
            user.groups.add(user.group)
            user.save()

        obj = UserProfile()

        from datetime import datetime
        import base64

        date = datetime.now().strftime("%Y%m%d-%H%M%S")
        img_data = base64.b64decode(profilepic)
        filename = date + ".jpg"
        file_path = "D:\\Riss_Projects_2025-26\\DONBOSCO Bca2\\zenbook_web\\media\\" + filename
        with open(file_path, "wb") as fh:
            fh.write(img_data)
        obj.profile_pic = "/media/" + filename


        obj.USER = user
        obj.location = location
        obj.gender = gender
        obj.phone = phone
        obj.dob = dob
        obj.save()

        return JsonResponse({'status': 'ok'})


# ================= Login ============================================





def user_login(request):
    if request.method == 'POST':
        name = request.POST['name']
        password = request.POST['password']

        print(request.POST)
        user = authenticate(request, username=name, password=password)

        print(user)

        if user is not None:

            try:
                blocked_user = BlockedUser.objects.get(user=user, is_blocked=True)
                return JsonResponse({
                    'status': 'blocked',
                    'message': 'Your account has been blocked for repeated violations.'
                })
            except BlockedUser.DoesNotExist:

                pass

            if user.groups.filter(name='user').exists():
                return JsonResponse({'status': 'ok', 'lid': str(user.id)})
            else:
                return JsonResponse({'status': 'no', 'message': 'User does not have required permissions.'})

        else:
            return JsonResponse({'status': 'no', 'message': 'Invalid credentials.'})

    return JsonResponse({'status': 'no', 'message': 'Invalid request method.'})

# ================ Logout ======================================

def logout_user(request):
    logout(request)
    return JsonResponse({'status': 'ok', 'message': 'Logged out successfully'})



# ======== view =================================================



def viewprofile(request):
    lid = request.POST['lid']

    data = UserProfile.objects.get(USER=lid)
    return JsonResponse({'status': 'ok',
                         'name':data.USER.username,
                         'first_name':data.USER.first_name,
                         'last_name': data.USER.last_name,
                         'profile_pic':data.profile_pic,
                         'phone':data.phone,
                         'gender':data.gender,
                         'email':data.USER.email,
                         'place': data.location,
                         'dob':data.dob,})



# ============ edit profile ============================


def editprofile(request):
    lid = request.POST['lid']

    user = User.objects.get(id=lid)
    profile = UserProfile.objects.get(USER=user)


    user.first_name = request.POST['first_name']
    user.last_name = request.POST['last_name']
    user.username = request.POST['username']
    user.email = request.POST['email']
    user.save()


    profile.phone = request.POST['phone']
    profile.gender = request.POST['gender']
    profile.location = request.POST['place']
    profile.dob = request.POST['dob']

    photo = request.POST.get('photos', '').strip()
    if photo:
        date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        img_data = base64.b64decode(photo)
        filename = date+ ".jpg"
        file_path = "D:\\Riss_Projects_2025-26\\DONBOSCO Bca2\\zenbook_web\\media\\" + filename
        with open(file_path, "wb") as fh:
            fh.write(img_data)
        profile.profile_pic = "/media/" + filename

    profile.save()
    return JsonResponse({'status': 'ok'})


# ==================== add_post ==========================


import base64
import datetime
import os
import torch
import numpy as np
from django.http import JsonResponse
from PIL import Image
from torchvision import transforms, models
from .models import User, Post

MODEL_PATH = r"D:\Riss_Projects_2025-26\DONBOSCO Bca2\zenbook_web\myapp\violence_model.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

checkpoint = torch.load(MODEL_PATH, map_location=device)
model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
model.fc = torch.nn.Linear(model.fc.in_features, len(checkpoint['classes']))
model.load_state_dict(checkpoint['model_state'])
model = model.to(device)
model.eval()
class_names = checkpoint['classes']


def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert("RGB")
    return transform(image).unsqueeze(0)

def predict(image_path):
    with torch.no_grad():
        image_tensor = preprocess_image(image_path).to(device)
        output = model(image_tensor)
        pred_idx = torch.argmax(output, dim=1).item()
        return class_names[pred_idx]


def add_post(request):
    if request.method == "POST":
        try:
            user_id = request.POST['user_id']
            content = request.POST['content']
            image_data = request.POST['image']
            post_date = request.POST['post_date']

            user = User.objects.get(id=user_id)


            date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            image_path = f"D:\\Riss_Projects_2025-26\\DONBOSCO Bca2\\zenbook_web\\media\\{date_str}.jpg"

            with open(image_path, "wb") as fh:
                fh.write(base64.b64decode(image_data))

            predicted_class = predict(image_path)

            if predicted_class.lower() != "normal":
                if os.path.exists(image_path):
                    os.remove(image_path)
                return JsonResponse({'status': 'error', 'message': f'🚫 This image contains {predicted_class} content and cannot be posted.'})

            post = Post(
                user=user,
                content=content,
                image=f"/media/{date_str}.jpg",
                post_date=post_date,
            )
            post.save()

            return JsonResponse({'status': 'ok', 'message': '✅ Post added successfully!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


# ==========view post===============================

def view_post(request):
    user_id = request.POST['lid']
    user = User.objects.get(id=user_id)
    post_data=[]

    posts = Post.objects.filter(user=user)

    for i in posts:
        post_data.append(
            {'id':i.id,
             'content':i.content,
             'photo':str(i.image),
             'post_date': i.post_date,
             'names': i.user.username}

        )


    return JsonResponse ({'status':'ok','data':post_data})


# ===================delete ====================

def deletepost(request):
    id = request.POST['id']
    Post.objects.get(id=id).delete()
    return JsonResponse({'status':"ok"})


# ============== view all post ====================================================

def view_all_post(request):

    post_data=[]
    lid=request.POST['lid']

    posts = Post.objects.exclude(user_id=lid)

    for i in posts:
        post_data.append(
            {'id':i.id,
             'names':i.user.username,
             'content':i.content,
             'photo':str(i.image),
             'post_date': i.post_date,})
    print(post_data)

    return JsonResponse ({'status':'ok','data':post_data})


#================like ===========================


def toggle_like(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        user_id = request.POST.get('user_id')
        post = Post.objects.get(id=post_id)
        user = User.objects.get(id=user_id)

        existing_like = Like.objects.filter(post=post, user=user)

        if existing_like.exists():
            existing_like.delete()
            liked = False
        else:
            L = Like()
            L.post = post
            L.user = user
            L.date = datetime.datetime.now().date()
            L.save()
            liked = True

        like_count = Like.objects.filter(post=post).count()

        return JsonResponse({
            'status': 'ok',
            'liked': liked,
            'like_count': like_count
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


# ======================== view like ==================================================


def view_like(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        posts = Post.objects.all()

        data = []
        for post in posts:
            like_count = Like.objects.filter(post=post).count()
            user_liked = Like.objects.filter(post=post, user_id=user_id).exists()

            data.append({
                'post_id': post.id,
                'like_count': like_count,
                'is_liked': user_liked,
            })

        return JsonResponse({'status': 'ok', 'data': data})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


#  ================== send complaints==================================================

#
def send_complaint(request):
    if request.method == 'POST':
        user_id = request.POST['lid']
        user = User.objects.get(id=user_id)
        complaint_text = request.POST['complaint']
        complaint=Complaint.objects.create(
            user=user,
            message=complaint_text,
            date=datetime.datetime.now().date(),
            status='Pending',
            reply='Pending',
        )
        complaint.save()
        return JsonResponse({'status': 'ok', 'message': 'Complaint sent successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})


# =================== view complaints==================================================
def view_complaints(request):
    if request.method == 'POST':
        lid = request.POST['lid']
        user = User.objects.get(id=lid)
        complaints = Complaint.objects.filter(user=user)

        data = []
        for c in complaints:
            data.append({
                'id': c.id,
                'message': c.message,
                'date': datetime.datetime.now().date(),
                'reply': c.reply or '',
                'status': c.status,
            })

        return JsonResponse({'status': 'ok', 'data': data})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})


# ===================== Notifications ================================================

from django.http import JsonResponse
from .models import Notification
from django.contrib.auth.models import User
import datetime

def view_notifications(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        user = User.objects.filter(id=lid).first()

        notifications = Notification.objects.all()
        data = []

        for n in notifications:
            data.append({
                'id': n.id,
                'text': n.text,
                'date': n.date or datetime.datetime.now().strftime('%Y-%m-%d'),
            })

        return JsonResponse({'status': 'ok', 'data': data})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})


# =============== delete ==============================================================

def delete_complaint(request):
    id = request.POST['id']
    Complaint.objects.get(id=id).delete()
    return JsonResponse({'status':"ok"})

# =====================================================================


# ============= view user===========
def view_all_users(request):
    if request.method == 'GET':
        lid = request.GET.get('lid')

        if lid:
            users = UserProfile.objects.exclude(USER__id=lid)
        else:
            users = UserProfile.objects.all()

        data = []

        current_user = User.objects.get(id=lid) if lid else None

        for user in users:

            status = 'none'
            if current_user:

                fr = FriendRequest.objects.filter(
                    (Q(sender=current_user) & Q(receiver=user.USER)) |
                    (Q(sender=user.USER) & Q(receiver=current_user))
                ).first()
                if fr:
                    status = fr.status

            data.append({
                'id': user.USER.id,
                'first_name': user.USER.first_name,
                'last_name': user.USER.last_name,
                'profile_pic': str(user.profile_pic),
                'friend_request_status': status,
            })

        return JsonResponse({'status': 'ok', 'users': data})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'})


# ============ send friend request=================================================

def send_friend_request(request):
    if request.method == 'POST':
        sender_id = request.POST.get('sender_id')
        receiver_id = request.POST.get('receiver_id')

        print(sender_id,receiver_id)
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        friend_request = FriendRequest.objects.create(
            sender=sender,
            receiver=receiver,
            status='pending'
        )
        friend_request.save()

        return JsonResponse({'status': 'ok', 'message': 'Friend request sent successfully'})

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})
# =============cancel request==================================================

def cancel_friend_request(request):
    if request.method == 'POST':
        sender_id = request.POST.get('sender_id')
        receiver_id = request.POST.get('receiver_id')

        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        # Delete all FriendRequest objects with this sender and receiver
        FriendRequest.objects.filter(sender=sender, receiver=receiver).delete()

        return JsonResponse({'status': 'ok', 'message': 'Friend request cancelled successfully'})

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})

# ============== view friend======================================================
from django.db.models import Q, Count

def view_friend_requests(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')  # Logged-in user ID (User.id)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})

        # Get all requests where this user is the receiver
        friend_requests = FriendRequest.objects.filter(receiver=user,status='pending')

        data = []
        for fr in friend_requests:
            try:
                sender_profile = fr.sender.userprofile  # Access related UserProfile
                profile_pic = sender_profile.profile_pic
            except UserProfile.DoesNotExist:
                profile_pic = ''

            data.append({
                'request_id': fr.id,
                'sender_id': fr.sender.id,
                'sender_first_name': fr.sender.first_name,
                'sender_last_name': fr.sender.last_name,
                'profile_pic': profile_pic,
                'status': fr.status,
            })

        return JsonResponse({'status': 'ok', 'friend_requests': data})

    return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'})




def view_friend_requestss(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')  # Logged-in user ID (User.id)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})

        # Get all requests where this user is the receiver
        friend_requests = FriendRequest.objects.filter(receiver=user,status ='pending')

        data = []
        for fr in friend_requests:
            try:
                sender_profile = fr.sender.userprofile  # Access related UserProfile
                profile_pic = sender_profile.profile_pic
            except UserProfile.DoesNotExist:
                profile_pic = ''

            data.append({
                'request_id': fr.id,
                'sender_id': fr.sender.id,
                'sender_first_name': fr.sender.first_name,
                'sender_last_name': fr.sender.last_name,
                'profile_pic': profile_pic,
                'status': fr.status,
            })

        return JsonResponse({'status': 'ok', 'friend_requests': data})

    return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'})


# ========================= comfirm request===============================

@csrf_exempt
def respond_friend_request(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        status = request.POST.get('status')

        if not request_id or not status:
            return JsonResponse({'status': 'error', 'message': 'Missing parameters'})

        try:
            fr = FriendRequest.objects.get(id=request_id)
            fr.status = status
            fr.save()
            return JsonResponse({'status': 'ok', 'message': f'Friend request {status}'})
        except FriendRequest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Friend request not found'})

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})


def delete_friend_request(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')

        if not request_id:
            return JsonResponse({'status': 'error', 'message': 'Request ID is required'})

        deleted_count, _ = FriendRequest.objects.filter(id=request_id).delete()

        if deleted_count > 0:
            return JsonResponse({'status': 'ok', 'message': 'Friend request deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Friend request not found'})

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})
# =============================================================================================




# ============= view friends =========================================================

# =========================================================================================

def view_friend_list(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'user_id parameter missing'}, status=400)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

        accepted_requests = FriendRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status='accepted'
        )

        friends = []
        for fr in accepted_requests:
            friend_user = fr.receiver if fr.sender == user else fr.sender
            try:
                profile = friend_user.userprofile
                profile_pic = profile.profile_pic if profile.profile_pic else ''
            except UserProfile.DoesNotExist:
                profile_pic = ''

            friends.append({
                'user_id': friend_user.id,
                'first_name': friend_user.first_name,
                'last_name': friend_user.last_name,
                'profile_pic': profile_pic,
            })

        return JsonResponse({'status': 'ok', 'friends': friends})

    return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'}, status=405)

# ===================================================================================================


# ==================== privat chat working=============================================









# ======================= group ==================================
def create_group(request):
    if request.method == 'POST':
        user_id = request.POST['lid']  # same key style as in send_complaint
        user = User.objects.get(id=user_id)
        group_name = request.POST['group_name']

        group = Group_create.objects.create(
            group_name=group_name,
            created_by=user,
            created_at=datetime.datetime.now()
        )
        group.save()

        return JsonResponse({'status': 'ok', 'message': 'Group created successfully', 'group_id': group.id})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})

# ==========================================================================


# == group list===============

def view_group_list(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        print("User ID:", user_id)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})

        created_groups = Group_create.objects.filter(created_by=user)
        member_groups = Group_create.objects.filter(
            members__user=user
        ).exclude(created_by=user)

        # Combine both querysets (union)
        all_groups = created_groups.union(member_groups).order_by('-created_at')

        data = []
        for group in all_groups:
            data.append({
                'group_id': group.id,
                'group_name': group.group_name,
                'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': f"{group.created_by.first_name} {group.created_by.last_name}",
            })

        return JsonResponse({'status': 'ok', 'groups': data})

    return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'})

# == view friends list============

from django.db.models import Q

def view_friends_for_group(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})

        friend_requests = FriendRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status='accepted'
        )

        data = []
        for fr in friend_requests:
            friend_user = fr.receiver if fr.sender == user else fr.sender

            try:
                profile = friend_user.userprofile
                profile_pic = profile.profile_pic
            except UserProfile.DoesNotExist:
                profile_pic = ''

            data.append({
                'request_id': fr.id,
                'sender_id': friend_user.id,
                'sender_first_name': friend_user.first_name,
                'sender_last_name': friend_user.last_name,
                'profile_pic': profile_pic,
                'status': fr.status,
            })

        return JsonResponse({'status': 'ok', 'friend_requests': data})

    return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'})


def add_group_member(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        user_id = request.POST.get('user_id')


        group = get_object_or_404(Group_create, id=group_id)
        user = get_object_or_404(User, id=user_id)

        if GroupMember.objects.filter(group=group, user=user).exists():
            return JsonResponse({'status': 'error', 'message': 'User already in group'})

        GroupMember.objects.create(group=group, user=user)

        return JsonResponse({'status': 'ok', 'message': 'Member added successfully'})

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})





#
# ================= group members list ========================================================




# =========================== ML   ====================================================================



from django.http import JsonResponse
from .models import GroupChat, Group_create
from django.contrib.auth.models import User
import datetime
import os
import speech_recognition as sr
from pydub import AudioSegment
import google.generativeai as genai
from .Eng_mang_train import ToxicityAnalyzer

#  Configure Gemini API
genai.configure(api_key='AIzaSyD3T4jvOPYo0_dEBPqOTF2IipCTpEegDUA')


toxicity_analyzer = None
analyzer_available = False
try:
    toxicity_analyzer = ToxicityAnalyzer()
    analyzer_available = True
    print("✅ Group Toxicity analyzer loaded successfully!")
except Exception as e:
    print(f"⚠️ Failed to load group toxicity analyzer: {e}")
    print("⚠️ Continuing without toxicity detection")


def translate_with_gemini(text):
    """Translate Malayalam/English/mixed text into English using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"Translate the following Malayalam/English mixed text into pure English:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return None


def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    wav_file = "temp_converted.wav"
    audio = AudioSegment.from_file(audio_path)
    audio.export(wav_file, format="wav")

    raw_text, english_text = "", ""
    try:
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
            raw_text = recognizer.recognize_google(audio_data, language="ml-IN")
            print(f"🎤 Raw Transcription: {raw_text}")

        english_text = translate_with_gemini(raw_text) or raw_text
        print(f"🌍 English Converted: {english_text}")

    except Exception as e:
        print(f"⚠️ Audio transcription error: {e}")

    finally:
        if os.path.exists(wav_file):
            os.remove(wav_file)

    return raw_text, english_text

def user_chat_send(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST method allowed"})

    from_id = request.POST.get("from_id")
    to_id = request.POST.get("to_id")
    message = request.POST.get("message", "").strip()
    audio_file = request.FILES.get("audio")

    try:
        sender = User.objects.get(id=from_id)
        receiver = User.objects.get(id=to_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    is_toxic = False
    detected_language = "unknown"
    toxic_english_words = []
    toxic_manglish_words = []
    raw_audio_text = ""
    english_audio_text = ""

    if message and not audio_file:
        if analyzer_available:
            try:
                toxicity, confidence, language, toxic_english, toxic_manglish, _ = (
                    toxicity_analyzer.analyze_toxicity(message)
                )
                is_toxic = (toxicity == "Toxic")
                detected_language = language
                toxic_english_words = toxic_english
                toxic_manglish_words = toxic_manglish

                if is_toxic:
                    print("\n🚨 TOXIC USER TEXT DETECTED!")
                    print(f"From: {sender.username} → To: {receiver.username}")
                    print(f"Message: {message}")
                    print(f"Confidence: {confidence:.1%} | Language: {language}")
            except Exception as e:
                print(f"⚠️ Error during toxicity analysis: {e}")

        chat = Chat.objects.create(
            FROMID=sender, TOID=receiver, msg=message, toxic=is_toxic, date=datetime.datetime.now().date()
        )

    elif audio_file:

        temp_path = f"temp_{audio_file.name}"
        with open(temp_path, "wb+") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)


        raw_audio_text, english_audio_text = transcribe_audio(temp_path)
        os.remove(temp_path)


        if analyzer_available and english_audio_text:
            try:
                toxicity, confidence, language, toxic_english, toxic_manglish, _ = (
                    toxicity_analyzer.analyze_toxicity(english_audio_text)
                )
                is_toxic = (toxicity == "Toxic")
                detected_language = language
                toxic_english_words = toxic_english
                toxic_manglish_words = toxic_manglish

                if is_toxic:
                    print("\n🚨 TOXIC USER AUDIO DETECTED!")
                    print(f"From: {sender.username} → To: {receiver.username}")
                    print(f"English Transcript: {english_audio_text}")
                    print(f"Confidence: {confidence:.1%} | Language: {language}")
            except Exception as e:
                print(f"⚠️ Toxicity analysis failed: {e}")

        chat = Chat.objects.create(
            FROMID=sender, TOID=receiver, msg="", audio=audio_file,
            toxic=is_toxic, date=datetime.datetime.now().date()
        )

    else:
        return JsonResponse({"status": "error", "message": "No message or audio provided"})

    # ------------------ RESPONSE ------------------
    return JsonResponse({
        "status": "ok",
        "id": chat.id,
        "message": chat.msg,
        "raw_audio_text": raw_audio_text,
        "english_audio_text": english_audio_text,
        "toxic": is_toxic,
        "language": detected_language,
        "toxic_english_words": toxic_english_words,
        "toxic_manglish_words": toxic_manglish_words,
        "audio": bool(audio_file)
    })


def chat_view_user(request):

    from_id = request.POST.get("from_id")
    to_id = request.POST.get("to_id")

    res = Chat.objects.filter(
        Q(FROMID_id=from_id, TOID_id=to_id) | Q(FROMID_id=to_id, TOID_id=from_id)
    ).select_related("FROMID", "TOID").order_by("id")

    chats = []
    for i in res:
        audio_url = None
        if i.audio and hasattr(i.audio, "url"):
            if os.path.exists(i.audio.path):  # safe check
                audio_url = request.build_absolute_uri(i.audio.url)

        chats.append({
            "id": i.id,
            "msg": i.msg,
            "to": i.TOID.id,
            "from": i.FROMID.id,
            "date": i.date.strftime("%Y-%m-%d"),
            "audio": audio_url,
            "toxic": i.toxic,
        })

    return JsonResponse({"status": "ok", "data": chats})


# ===================== group ==============================================


# ==================================================================================================

from django.http import JsonResponse
from .models import GroupChat, Group_create
from django.contrib.auth.models import User
import datetime
import os
import speech_recognition as sr
from pydub import AudioSegment
import google.generativeai as genai
from .Eng_mang_train import ToxicityAnalyzer


# ✅ Configure Gemini API
genai.configure(api_key='AIzaSyD3T4jvOPYo0_dEBPqOTF2IipCTpEegDUA')


toxicity_analyzer = None
analyzer_available = False
try:
    toxicity_analyzer = ToxicityAnalyzer()
    analyzer_available = True
    print("✅ Group Toxicity analyzer loaded successfully!")
except Exception as e:
    print(f"⚠️ Failed to load group toxicity analyzer: {e}")
    print("⚠️ Continuing without toxicity detection")


def translate_with_gemini(text):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"Translate the following Malayalam/English mixed text into pure English:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return None


def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    wav_file = "temp_converted.wav"
    audio = AudioSegment.from_file(audio_path)
    audio.export(wav_file, format="wav")

    raw_text, english_text = "", ""
    try:

        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
            raw_text = recognizer.recognize_google(audio_data, language="ml-IN")
            print(f"🎤 Raw Transcription: {raw_text}")

        english_text = translate_with_gemini(raw_text) or raw_text
        print(f"🌍 English Converted: {english_text}")

    except Exception as e:
        print(f"⚠️ Audio transcription error: {e}")

    finally:
        if os.path.exists(wav_file):
            os.remove(wav_file)

    return raw_text, english_text


def group_chat_send(request):

    if request.method == "POST":
        group_id = request.POST.get("group_id")
        sender_id = request.POST.get("sender_id")
        message = request.POST.get("message", "").strip()
        audio_file = request.FILES.get("audio")

        try:
            group = Group_create.objects.get(id=group_id)
            sender = User.objects.get(id=sender_id)
        except (Group_create.DoesNotExist, User.DoesNotExist):
            return JsonResponse({"status": "error", "message": "Group or User not found"})

        is_toxic = False
        detected_language = "unknown"
        toxic_english_words = []
        toxic_manglish_words = []

        # ------------------ TEXT MESSAGE ------------------
        if message and not audio_file:
            if analyzer_available:
                try:
                    toxicity, confidence, language, toxic_english, toxic_manglish, _ = (
                        toxicity_analyzer.analyze_toxicity(message)
                    )
                    is_toxic = (toxicity == "Toxic")
                    detected_language = language
                    toxic_english_words = toxic_english
                    toxic_manglish_words = toxic_manglish

                    if is_toxic:
                        print("\n🚨 TOXIC TEXT DETECTED!")
                        print(f"Group: {group_id} | Sender: {sender.username}")
                        print(f"Message: {message}")
                except Exception as e:
                    print(f"⚠️ Error during toxicity analysis: {e}")

            chat = GroupChat.objects.create(
                group=group, sender=sender, message=message, toxic=is_toxic
            )

        # ------------------ AUDIO MESSAGE ------------------
        elif audio_file:

            temp_path = f"temp_{audio_file.name}"
            with open(temp_path, "wb+") as f:
                for chunk in audio_file.chunks():
                    f.write(chunk)


            raw_text, english_text = transcribe_audio(temp_path)
            os.remove(temp_path)

            if analyzer_available and english_text:
                try:
                    toxicity, confidence, language, toxic_english, toxic_manglish, _ = (
                        toxicity_analyzer.analyze_toxicity(english_text)
                    )
                    is_toxic = (toxicity == "Toxic")
                    detected_language = language
                    toxic_english_words = toxic_english
                    toxic_manglish_words = toxic_manglish
                except Exception as e:
                    print(f"⚠️ Toxicity analysis failed: {e}")


            chat = GroupChat.objects.create(
                group=group, sender=sender, message="", audio=audio_file, toxic=is_toxic
            )

        else:
            return JsonResponse({"status": "error", "message": "No message or audio provided"})

        # ------------------ RESPONSE ------------------
        return JsonResponse({
            "status": "ok",
            "message_id": chat.id,
            "toxic": is_toxic,
            "language": detected_language,
            "toxic_english_words": toxic_english_words,
            "toxic_manglish_words": toxic_manglish_words,
            "audio": bool(audio_file)
        })

    return JsonResponse({"status": "error", "message": "Only POST method allowed"})

# ========================================================================

def group_chat_view(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        user_id = request.POST.get('user_id')

        chats = GroupChat.objects.filter(group_id=group_id).order_by("id")

        messages = []
        for chat in chats:
            audio_url = ""
            if chat.audio:
                if os.path.exists(chat.audio.path):
                    audio_url = request.build_absolute_uri(chat.audio.url)
                else:
                    print(f"File does not exist: {chat.audio.path}")

            messages.append({
                "id": chat.id,
                "sender_id": chat.sender.id,
                "sender_name": f"{chat.sender.first_name} {chat.sender.last_name}",
                "message": chat.message,
                "timestamp": chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "audio": audio_url,
                "toxic": chat.toxic
            })

        return JsonResponse({"status": "ok", "group_id": group_id, "messages": messages})

    return JsonResponse({"status": "error", "message": "Only POST method allowed"})

def view_group_members(request):
    if request.method == 'GET':
        group_id = request.GET.get('group_id')

        try:
            group = Group_create.objects.get(id=group_id)
        except Group_create.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Group not found'}, status=404)

        members = GroupMember.objects.filter(group=group).select_related('user')

        data = []
        for member in members:
            user = member.user
            try:
                profile = user.userprofile
                profile_pic = profile.profile_pic if profile.profile_pic else ''
            except UserProfile.DoesNotExist:
                profile_pic = ''

            data.append({
                'user_id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_pic': profile_pic,
            })

        return JsonResponse({'status': 'ok', 'group_name': group.group_name, 'members': data})

    return JsonResponse({'status': 'error', 'message': 'Only GET method allowed'}, status=405)

# ====================================== comments ===========================

import datetime
from django.http import JsonResponse
from .models import Post, Comment, User, Warning
from .Eng_mang_train import ToxicityAnalyzer

# Initialize toxicity analyzer
toxicity_analyzer = None
analyzer_available = False
try:
    toxicity_analyzer = ToxicityAnalyzer()
    analyzer_available = True
    print("✅ Toxicity analyzer loaded successfully for comments!")
except Exception as e:
    print(f"⚠️ Failed to load toxicity analyzer: {e}")


# ===================== POST COMMENT ============================
def user_comment_post(request):
    if request.method == 'POST':
        post_id = request.POST['post_id']
        user_id = request.POST['user_id']
        comment_text = request.POST['comment_text'].strip()

        try:
            post = Post.objects.get(id=post_id)
            user = User.objects.get(id=user_id)


            try:
                blocked_user = BlockedUser.objects.get(user=user, is_blocked=True)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your account has been blocked for repeated violations.'
                })
            except BlockedUser.DoesNotExist:
                pass

        except (Post.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': 'Post or user not found.'
            })

        is_toxic = False
        toxic_words = []

        if analyzer_available and comment_text:
            try:
                toxicity, confidence, language, toxic_english, toxic_manglish, neutral_words = (
                    toxicity_analyzer.analyze_toxicity(comment_text)
                )
                is_toxic = (toxicity == "Toxic")
                toxic_words = toxic_english + toxic_manglish
            except Exception as e:
                print(f"⚠️ Error in toxicity analysis: {e}")


        comment = Comment.objects.create(
            post=post,
            user=user,
            comment_text=comment_text,
            date=datetime.datetime.now().date(),
            toxic=is_toxic
        )

        if is_toxic:
            Warning.objects.create(
                user=user,
                comment=comment,
                warning_message="⚠️ Inappropriate comment detected."
            )

            warning_count = Warning.objects.filter(user=user).count()

            if warning_count >= 3:

                blocked_user, created = BlockedUser.objects.get_or_create(
                    user=user,
                    defaults={'is_blocked': True, 'reason': '3 toxic comments detected'}
                )

                if not created:
                    blocked_user.is_blocked = True
                    blocked_user.reason = '3 toxic comments detected'
                    blocked_user.blocked_at = datetime.timezone.now()
                    blocked_user.save()

                return JsonResponse({
                    'status': 'blocked',
                    'message': 'Your account has been blocked for repeated violations.',
                    'toxic': is_toxic,
                    'toxic_words': toxic_words,
                    'warning_count': warning_count
                })

        return JsonResponse({
            'status': 'ok',
            'message': 'Comment added successfully',
            'toxic': is_toxic,
            'toxic_words': toxic_words,
            'warning_count': Warning.objects.filter(user=user).count()
        })
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
# ===================== DUPLICATE (comment_post) ============================
def comment_post(request):
    if request.method == 'POST':
        post_id = request.POST['post_id']
        user_id = request.POST['user_id']
        comment_text = request.POST['comment_text'].strip()

        try:
            post = Post.objects.get(id=post_id)
            user = User.objects.get(id=user_id)
            try:
                blocked_user = BlockedUser.objects.get(user=user, is_blocked=True)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your account has been blocked for repeated violations.'
                })
            except BlockedUser.DoesNotExist:
                # User is not blocked, continue
                pass

        except (Post.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': 'Post or user not found.'
            })

        is_toxic = False
        toxic_words = []

        if analyzer_available and comment_text:
            try:
                toxicity, confidence, language, toxic_english, toxic_manglish, neutral_words = (
                    toxicity_analyzer.analyze_toxicity(comment_text)
                )
                is_toxic = (toxicity == "Toxic")
                toxic_words = toxic_english + toxic_manglish
            except Exception as e:
                print(f"⚠️ Error in toxicity analysis: {e}")


        comment = Comment.objects.create(
            post=post,
            user=user,
            comment_text=comment_text,
            date=datetime.datetime.now().date(),
            toxic=is_toxic
        )


        if is_toxic:
            Warning.objects.create(
                user=user,
                comment=comment,
                warning_message="⚠️ Inappropriate comment detected."
            )


            warning_count = Warning.objects.filter(user=user).count()

            if warning_count >= 3:

                blocked_user, created = BlockedUser.objects.get_or_create(
                    user=user,
                    defaults={'is_blocked': True, 'reason': '3 toxic comments detected'}
                )

                if not created:
                    blocked_user.is_blocked = True
                    blocked_user.reason = '3 toxic comments detected'
                    blocked_user.blocked_at = datetime.timezone.now()  # Update the blocked time
                    blocked_user.save()

                return JsonResponse({
                    'status': 'blocked',
                    'message': 'Your account has been blocked for repeated violations.',
                    'toxic': is_toxic,
                    'toxic_words': toxic_words,
                    'warning_count': warning_count
                })

        return JsonResponse({
            'status': 'ok',
            'message': 'Comment added successfully',
            'toxic': is_toxic,
            'toxic_words': toxic_words,
            'warning_count': Warning.objects.filter(user=user).count()
        })
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
# ===================== VIEW COMMENTS ============================
def view_comments(request):
    postid = request.POST.get('pid')

    try:
        post = Post.objects.get(id=postid)
    except Post.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid post_id'})

    comments = Comment.objects.filter(post=post).select_related("user")

    comment_data = []
    for c in comments:
        comment_data.append({
            'comment_id': c.id,
            'user': c.user.username,
            'comment_text': c.comment_text,
            'date': str(c.date),
            'toxic': c.toxic,
        })

    return JsonResponse({'status': 'ok', 'data': comment_data})


def view_warnings(request):
    """Fetch all warnings for a user"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST method allowed"})

    user_id = request.POST.get("user_id")
    user = User.objects.get(id=user_id)
    warnings = Warning.objects.filter(user=user).order_by("-date")

    data = []
    for w in warnings:
        data.append({
            "id": w.id,
            "comment_id": w.comment.id if w.comment else None,
            "warning_message": w.warning_message,
            "date": w.date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return JsonResponse({"status": "ok", "warnings": data})




# ======================================================================================================================================