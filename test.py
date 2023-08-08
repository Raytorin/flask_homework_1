import re


def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(pattern, str(email)):
        return True
    else:
        return False


email = test@mail.ru

if validate_email(email):
    print("Email введен верно.")
else:
    print("Email введен неверно.")