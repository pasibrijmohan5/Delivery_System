from django.contrib.auth import get_user_model
from main.models import Order
from accounts.models import DeliveryPerson

User = get_user_model()
print("--- Diagnostic Report ---")

# 1. List all Delivery Riders
riders = DeliveryPerson.objects.all()
print(f"Total Riders: {riders.count()}")
for r in riders:
    assigned_count = Order.objects.filter(delivery_person=r).count()
    active_count = Order.objects.filter(delivery_person=r).exclude(status=Order.Status.DELIVERED).count()
    print(f"Rider ID: {r.id} | User: {r.user.email} | Total Assigned: {assigned_count} | Active: {active_count}")

# 2. List all Orders with a Delivery Person
orders_with_rider = Order.objects.exclude(delivery_person__isnull=True)
print(f"\nOrders with Riders assigned: {orders_with_rider.count()}")
for o in orders_with_rider:
    print(f"Order: {o.order_id} | Status: {o.status} | Assigned to Rider: {o.delivery_person.user.email} (Rider ID: {o.delivery_person.id})")

# 3. Check for users with roles but no profiles
users_with_role = User.objects.filter(role='delivery_person')
for u in users_with_role:
    has_profile = hasattr(u, 'delivery_profile')
    print(f"User: {u.email} | Role: {u.role} | Has Profile: {has_profile}")
