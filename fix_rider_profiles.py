from accounts.models import CustomUser, DeliveryPerson
riders = CustomUser.objects.filter(role=CustomUser.Roles.DELIVERY_PERSON)
count = 0
for u in riders:
    rider, created = DeliveryPerson.objects.get_or_create(user=u)
    if created:
        count += 1
print(f"Created {count} missing DeliveryPerson profiles.")
