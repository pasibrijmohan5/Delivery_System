from accounts.models import CustomUser, DeliveryPerson
from main.models import Order

email = "bibek6084@gmail.com" # The user I saw in diagnostic
user = CustomUser.objects.get(email=email)
rider = user.delivery_profile

print(f"User: {user.email} | Role: {user.role}")
print(f"Rider Profile ID: {rider.id}")

# Find an order and assign it
order = Order.objects.first()
if order:
    print(f"Assigning Order {order.order_id} to Rider {rider.id}...")
    order.delivery_person = rider
    order.status = Order.Status.ON_THE_WAY
    order.save()
    
    # Verify assignment
    order.refresh_from_db()
    print(f"Order {order.order_id} delivery_person_id: {order.delivery_person_id}")
    
    # Test filtering as used in views.py
    assigned = Order.objects.filter(delivery_person=rider)
    print(f"Orders found via direct filter: {assigned.count()}")
    for a in assigned:
        print(f" - Found: {a.order_id}")
        
    # Test filtering as used in api_views.py
    api_filtered = Order.objects.filter(delivery_person__user=user)
    print(f"Orders found via API filter (user): {api_filtered.count()}")
else:
    print("No order found to test with.")
