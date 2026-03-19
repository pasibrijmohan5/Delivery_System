from accounts.models import CustomUser
users = CustomUser.objects.all()
print("ID | Email | Role | Is Staff")
for u in users:
    print(f"{u.id} | {u.email} | {u.role} | {u.is_staff}")
