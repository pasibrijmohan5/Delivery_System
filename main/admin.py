from django.contrib import admin
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Category, Product, Order, OrderItem, Payment, Review
from accounts.models import DeliveryPerson

admin.site.register(Category)
admin.site.register(Product)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'status', 'total', 'created_at', 'delivery_person')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'user__email')
    raw_id_fields = ('user',)
    actions = ['forward_orders']

    @admin.action(description="Forward selected orders to a Delivery Rider")
    def forward_orders(self, request, queryset):
        if 'apply' in request.POST:
            rider_id = request.POST.get('rider')
            selected_ids = request.POST.getlist('_selected_action')
            try:
                rider = DeliveryPerson.objects.get(id=rider_id)
                orders_to_update = Order.objects.filter(id__in=selected_ids)
                count = 0
                for order in orders_to_update:
                    order.delivery_person = rider
                    if order.status in [Order.Status.PENDING, Order.Status.PAID]:
                        order.status = Order.Status.ON_THE_WAY
                    order.save()
                    count += 1
                self.message_user(request, f"Successfully forwarded {count} order(s) to Rider: {rider}.", messages.SUCCESS)
                return HttpResponseRedirect(request.path)
            except DeliveryPerson.DoesNotExist:
                self.message_user(request, "Selected rider does not exist.", messages.ERROR)
        
        riders = DeliveryPerson.objects.filter(is_active=True)
        return render(request, 'admin/forward_orders.html', {'orders': queryset, 'riders': riders})
    
    def save_model(self, request, obj, form, change):
        if change and 'delivery_person' in form.changed_data and obj.delivery_person:
            if obj.status in [Order.Status.PENDING, Order.Status.PAID]:
                obj.status = Order.Status.ON_THE_WAY
        super().save_model(request, obj, form, change)

admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Review)
