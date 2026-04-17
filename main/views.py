from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
import requests
import uuid
import json
from .models import Product, Category, Order, OrderItem, Payment
from accounts.models import DeliveryPerson, CustomUser, ShippingAddress

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
    if request.user.role == CustomUser.Roles.ADMIN:
        return redirect('main:admin_dashboard')
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
    
    if request.user.role == CustomUser.Roles.ADMIN:
        return JsonResponse({'error': 'Admins cannot place orders.'}, status=403)

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


def _get_khalti_secret_key():
    """
    Helper to get and sanitize the Khalti secret key.
    Strips prefixes if present as required by some Khalti environments.
    """
    secret_key = str(settings.KHALTI_SECRET_KEY).strip()
    for prefix in ['test_secret_key_', 'live_secret_key_']:
        if secret_key.startswith(prefix):
            secret_key = secret_key[len(prefix):]
            break
    return secret_key


@login_required
def initiate_khalti_payment(request):
    """
    Initiates a Khalti payment by creating an order and calling the Khalti initiate API.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        shipping_data = data.get('shipping_address')
        
        # 1. Get cart items
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({'error': 'Your cart is empty'}, status=400)

        # 2. Calculate totals and prepare items
        subtotal = 0
        order_items_to_create = []
        for pid, quantity in cart.items():
            product = Product.objects.get(id=int(pid))
            price = product.price
            subtotal += price * quantity
            order_items_to_create.append({
                'product': product,
                'name': product.name,
                'price': price,
                'quantity': quantity
            })

        shipping_cost = 50
        total = subtotal + shipping_cost

        # 3. Handle Shipping Address
        shipping_address = None
        if shipping_data:
            shipping_address, _ = ShippingAddress.objects.update_or_create(
                user=request.user,
                defaults={
                    'full_name': shipping_data.get('full_name', request.user.get_full_name()),
                    'phone': shipping_data.get('phone', ''),
                    'address_line': shipping_data.get('address_line', ''),
                    'location_name': shipping_data.get('location_name', ''),
                    'landmark': shipping_data.get('landmark', ''),
                    'city': shipping_data.get('city', ''),
                    'postal_code': shipping_data.get('postal_code', '00000'),
                }
            )

        # 4. Create Order
        order = Order.objects.create(
            user=request.user,
            order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            shipping_address=shipping_address
        )

        for item in order_items_to_create:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                product_name=item['name'],
                price=item['price'],
                quantity=item['quantity']
            )

        # 5. Call Khalti Initiate API
        secret_key = _get_khalti_secret_key()
        
        if not secret_key or secret_key == 'None':
             return JsonResponse({
                'error': 'KHALTI_SECRET_KEY is missing in .env file.'
            }, status=400)

        khalti_url = f"{settings.KHALTI_BASE_URL}epayment/initiate/"
        headers = {
            'Authorization': f'Key {secret_key}',
            'Content-Type': 'application/json',
        }
        
        # Use full URL for return_url
        return_url = request.build_absolute_uri(reverse('main:verify_khalti'))
        
        payload = {
            "return_url": return_url,
            "website_url": request.build_absolute_uri('/'),
            "amount": int(total * 100), # Paisa
            "purchase_order_id": order.order_id,
            "purchase_order_name": f"Order {order.order_id}",
            "customer_info": {
                "name": (request.user.get_full_name() or request.user.email).strip(),
                "email": request.user.email.strip(),
                "phone": shipping_data.get('phone', '9800000000').strip()
            }
        }

        # DIAGNOSTIC LOGGING
        print(f"--- KHALTI INITIATE DEBUG ---")
        print(f"URL: {khalti_url}")
        print(f"Key Length: {len(secret_key)}")
        print(f"Key Starts: {secret_key[:18]}...")
        
        response = requests.post(khalti_url, headers=headers, json=payload)
        resp_data = response.json()

        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {resp_data}")
        print(f"-----------------------------")

        if response.status_code == 200:
            # 6. Create Payment Record (Initiated) - ONLY after getting valid pidx
            payment = Payment.objects.create(
                order=order,
                method=Payment.Method.KHALTI,
                status=Payment.Status.INITIATED,
                purchase_order_id=order.order_id,
                transaction_id=f"INIT-{order.order_id}", # Global unique placeholder
                pidx=resp_data.get('pidx'),
                amount=total
            )
            
            return JsonResponse({
                'payment_url': resp_data.get('payment_url'),
                'pidx': resp_data.get('pidx')
            })
        else:
            error_msg = f"Khalti API Error ({response.status_code})"
            if response.status_code == 401:
                error_msg += ": Invalid Token. Please ensure your Secret Key is correct and that ePayment is enabled in your Khalti Merchant Dashboard."
            
            return JsonResponse({
                'error': error_msg,
                'details': resp_data
            }, status=response.status_code)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def verify_khalti_payment(request):
    """
    Verifies the Khalti payment using the pidx provided in the redirect.
    """
    pidx = request.GET.get('pidx') or request.GET.get('pid') # Handle both standard and variations
    
    if not pidx:
        return render(request, 'main/payment_status.html', {
            'status': 'error',
            'message': 'No payment identifier found.'
        })

    try:
        # 1. Verification API call
        secret_key = _get_khalti_secret_key()
        khalti_url = f"{settings.KHALTI_BASE_URL}epayment/lookup/"
        headers = {
            'Authorization': f'Key {secret_key}',
            'Content-Type': 'application/json',
        }
        payload = {"pidx": pidx}
        
        # DIAGNOSTIC LOGGING
        print(f"--- KHALTI VERIFY DEBUG ---")
        print(f"URL: {khalti_url}")
        print(f"PIDX: {pidx}")
        
        response = requests.post(khalti_url, headers=headers, json=payload)
        resp_data = response.json()

        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {resp_data}")
        print(f"---------------------------")

        if response.status_code == 200 and resp_data.get('status') == 'Completed':
            # 2. Update Payment and Order
            try:
                payment = Payment.objects.get(pidx=pidx)
                order = payment.order
                
                payment.status = Payment.Status.SUCCESS
                payment.transaction_id = resp_data.get('transaction_id')
                payment.save()
                
                order.status = Order.Status.PAID
                order.save()
                
                # 3. Clear Cart
                if 'cart' in request.session:
                    del request.session['cart']
                    request.session.modified = True
                
                return render(request, 'main/payment_status.html', {
                    'status': 'success',
                    'order': order,
                    'transaction_id': payment.transaction_id
                })
            except Payment.DoesNotExist:
                return render(request, 'main/payment_status.html', {
                    'status': 'error',
                    'message': 'Payment record not found.'
                })
        else:
            # Check if it was already successful in our DB but Khalti lookup failed or returned something else
            try:
                payment = Payment.objects.get(pidx=pidx)
                if payment.status == Payment.Status.SUCCESS:
                    return render(request, 'main/payment_status.html', {
                        'status': 'success',
                        'order': payment.order,
                        'transaction_id': payment.transaction_id
                    })
            except Payment.DoesNotExist:
                pass

            return render(request, 'main/payment_status.html', {
                'status': 'failed',
                'message': resp_data.get('status', 'Payment could not be verified.')
            })

    except Exception as e:
        return render(request, 'main/payment_status.html', {
            'status': 'error',
            'message': str(e)
        })