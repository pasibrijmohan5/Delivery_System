from accounts.models import CustomUser, DeliveryPerson

riders = CustomUser.objects.filter(role=CustomUser.Roles.DELIVERY_PERSON)
for rider in riders:
    DeliveryPerson.objects.get_or_create(
        user=rider,
        defaults={
            'phone_number': 'N/A',
            'vehicle_type': DeliveryPerson.VehicleType.BICYCLE,
            'vehicle_plate_number': 'N/A'
        }
    )
print(f"Fixed {riders.count()} delivery rider profiles!")
