from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class CyberCell(models.Model):
    USER= models.OneToOneField(User,on_delete=models.CASCADE)
    phone=models.CharField(max_length=15)
    designation=models.CharField(max_length=200)





class UserProfile(models.Model):
    USER=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic=models.CharField(max_length=500,default='')
    location=models.CharField(max_length=200)
    gender=models.CharField(max_length=200,default='male')
    phone=models.CharField(max_length=200,null=True,blank=True)
    dob=models.CharField(max_length=200,null=True,blank=True)



class Post(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    content=models.TextField()
    image=models.FileField(upload_to='post_images/',null=True,blank=True)
    post_date=models.CharField(max_length=100)

    STATUS_CHOICES=(
        ('normal','normal'),
        ('bullying','bullying'),
        ('flagged','flagged')
    )
    status=models.CharField(max_length=100,choices=STATUS_CHOICES,default='normal')


class Comment(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE, related_name='comments')
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    comment_text=models.TextField()
    date = models.CharField(max_length=100,null=True)
    toxic = models.BooleanField(default=False)



class Like(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE, related_name='like')
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    date = models.CharField(max_length=100)



class Complaint(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    message=models.TextField()
    date=models.CharField(max_length=100)
    reply=models.TextField(blank=True,null=True)
    status=models.CharField(max_length=100,default="Pending")


class Notification(models.Model):
    text = models.TextField()
    date = models.CharField(max_length=100)



class FriendRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )


class Chat(models.Model):
    date = models.DateField()
    msg = models.CharField(max_length=50)
    audio = models.FileField(upload_to='chat_audio/', blank=True, null=True)
    FROMID = models.ForeignKey(User, on_delete=models.CASCADE,related_name='fromuser')
    TOID = models.ForeignKey(User, on_delete=models.CASCADE,related_name='touser')
    toxic = models.BooleanField(default=False)



# ===================================================================================

class Group_create(models.Model):
    group_name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)


class GroupMember(models.Model):
    group = models.ForeignKey(Group_create, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)


class GroupChat(models.Model):

    group = models.ForeignKey(Group_create, on_delete=models.CASCADE, related_name='chats')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_messages')
    message = models.TextField()
    file = models.FileField(upload_to='group_files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    audio = models.FileField(upload_to='group_chat_audio/', blank=True, null=True)
    toxic = models.BooleanField(default=False)


class BlockedUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_status")
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(default="Multiple toxic comments detected")

class Warning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="warnings")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    warning_message = models.CharField(max_length=255, default="Inappropriate comment detected.")
    date = models.DateTimeField(auto_now_add=True)
