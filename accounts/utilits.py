from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_notification_email(subject, template, context, recipient_list):
    text_content = render_to_string(f"emails/{template}.txt", context)
    html_content = render_to_string(f"emails/{template}.html", context)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
    )
    email.attach_alternative(html_content, "text/html")
    email.send()