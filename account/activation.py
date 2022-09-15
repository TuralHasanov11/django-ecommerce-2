from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from account import tokens

def sendEmailConfirmation(user):
    subject = 'Activate your Account'
    message = render_to_string('account/auth/activation_email.html', {
        'user': user,
        'domain': "",
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': tokens.account_activation_token.make_token(user),
    })
    user.email_user(subject=subject, message=message)