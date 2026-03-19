from accounts.models import CustomUser
riders = CustomUser.objects.filter(role='delivery_person')
count = 0
for r in riders:
    if not r.is_staff:
        r.is_staff = True
        r.save()
        count += 1
print(f"Updated {count} riders to staff status.")
