from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, Category, Order
from accounts.models import DeliveryPerson, CustomUser

def home(request):
    if request.user.is_authenticated:
        if request.GET.get('view') == 'user':
            pass
        elif request.user.role == CustomUser.Roles.DELIVERY_PERSON and request.session.get('rider_mode', True):
            return redirect('main:rider_dashboard')
        elif request.user.role == CustomUser.Roles.ADMIN:
            return redirect('main:admin_dashboard')

    categories = Category.objects.all()
    featured_products = Product.objects.filter(featured=True)[:4]
    menu_products = Product.objects.all()
    rider_tasks_count = 0

    if request.user.is_authenticated and request.user.role == 'delivery_person':
        try:
            rider = DeliveryPerson.objects.get(user=request.user)
            rider_tasks_count = Order.objects.filter(
                delivery_person=rider
            ).exclude(status=Order.Status.DELIVERED).count()
        except DeliveryPerson.DoesNotExist:
            pass

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'menu_products': menu_products,
        'rider_tasks_count': rider_tasks_count,
    }
    return render(request, 'main/home.html', context)


@login_required
def checkout(request):
    return render(request, 'main/checkout.html')


@login_required
def my_orders(request):
    personal_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    deliveries = []

    if request.user.role == CustomUser.Roles.DELIVERY_PERSON:
        try:
            rider = DeliveryPerson.objects.get(user=request.user)
            deliveries = Order.objects.filter(delivery_person=rider).exclude(
                status=Order.Status.DELIVERED
            ).order_by('-created_at')
        except DeliveryPerson.DoesNotExist:
            pass

    context = {
        'orders': personal_orders,
        'deliveries': deliveries
    }
    return render(request, 'main/my_orders.html', context)


@login_required
def toggle_rider_mode(request):
    if request.user.role == CustomUser.Roles.DELIVERY_PERSON:
        current_mode = request.session.get('rider_mode', True)
        request.session['rider_mode'] = not current_mode
    return redirect('main:home')


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login first'}, status=401)

    try:
        product = Product.objects.get(id=product_id)
        cart = request.session.get('cart', {})

        pid = str(product_id)
        if pid in cart:
            cart[pid] += 1
        else:
            cart[pid] = 1

        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({
            'status': 'success',
            'cart_count': sum(cart.values()),
            'message': f'{product.name} added to cart'
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        request.session['cart'] = cart
        request.session.modified = True
    return JsonResponse({'status': 'success'})


def get_cart(request):
    cart = request.session.get('cart', {})
    items = []
    subtotal = 0

    for pid, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(pid))
            total = float(product.price) * quantity
            subtotal += total
            items.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'total': total,
                'image_url': product.image.url if product.image else ''
            })
        except Product.DoesNotExist:
            continue

    return JsonResponse({
        'items': items,
        'subtotal': subtotal
    })


@login_required
def admin_dashboard(request):
    if request.user.role != CustomUser.Roles.ADMIN:
        return render(request, 'main/home.html', {'error': 'Unauthorized'})

    dishes = Product.objects.all().order_by('-created_at')
    orders = Order.objects.all().order_by('-created_at')
    riders = DeliveryPerson.objects.all()
    categories = Category.objects.all()

    context = {
        'dishes': dishes,
        'orders': orders,
        'riders': riders,
        'categories': categories,
    }
    return render(request, 'main/admin_dashboard.html', context)


@login_required
def rider_dashboard(request):
    if request.user.role != CustomUser.Roles.DELIVERY_PERSON:
        return render(request, 'main/home.html', {'error': 'Unauthorized'})

    try:
        rider = DeliveryPerson.objects.get(user=request.user)
        assigned_orders = Order.objects.filter(
            delivery_person=rider
        ).select_related('shipping_address', 'payment').order_by('-created_at')
    except DeliveryPerson.DoesNotExist:
        assigned_orders = []

    return render(request, 'main/rider_dashboard.html', {'orders': assigned_orders})
def menu_page(request):
    categories = Category.objects.all()
    products = Product.objects.all().order_by('name')

    context = {
        'categories': categories,
        'products': products,
    }
    return render(request, 'main/menu.html', context)