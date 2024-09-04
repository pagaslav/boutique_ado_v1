from django.shortcuts import render, redirect, reverse
from django.contrib import messages

from .forms import OrderForm


def checkout(request):
    bag = request.session.get('bag', {})
    if not bag:
        messages.error(request, "There's nothing in your bag at the moment")
        return redirect(reverse('products'))

    order_form = OrderForm()
    template = 'checkout/checkout.html'
    context = {
        'order_form': order_form,
        'stripe_public_key': 'pk_test_51PvKZTL6nonxjnriSrZSz1Jtniv04iZFZfJvvRW7qSN85mYyigmL3pw4GZFyBpDXcbtQncsNOoL3jLlKdYbyda4W00gdxy5C1l',
        'client_secret': 'sk_test_51PvKZTL6nonxjnriVLkWIuWmyutSTbtVpHjfvrEGenQ4WBNvij88RBRyZ963mYwtlczorNqlBeDLcyGkr6jMSGLP00picGYnBu',
    }

    return render(request, template, context)
