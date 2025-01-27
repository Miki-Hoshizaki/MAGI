from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task
def send_verification_email(user_id: int, verification_token: str):
    """Send email verification link to user."""
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        subject = 'Verify your email address'
        html_message = render_to_string('users/email/verify_email.html', {
            'user': user,
            'token': verification_token
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message
        )
        return True
    except User.DoesNotExist:
        return False


@shared_task
def send_password_reset_email(user_id: int, reset_token: str):
    """Send password reset link to user."""
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        subject = 'Reset your password'
        html_message = render_to_string('users/email/reset_password.html', {
            'user': user,
            'token': reset_token
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message
        )
        return True
    except User.DoesNotExist:
        return False


@shared_task
def cleanup_expired_tokens():
    """Remove expired verification and password reset tokens."""
    from django.utils import timezone
    from datetime import timedelta
    
    # This is a placeholder for token cleanup logic
    # Implement according to your token storage method
    pass


@shared_task
def send_welcome_email(user_id: int):
    """Send welcome email to newly registered user."""
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        subject = 'Welcome to Magi'
        html_message = render_to_string('users/email/welcome.html', {
            'user': user
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message
        )
        return True
    except User.DoesNotExist:
        return False 