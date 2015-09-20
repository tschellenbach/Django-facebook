1. Create facebook app and authorize url yourdomain.com
2. Add line: "127.0.0.1 local.yourdomain.com" to /etc/hosts
3. Add your facebook app id and app secret to variables FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in settings.py
4. python manage.py runserver
