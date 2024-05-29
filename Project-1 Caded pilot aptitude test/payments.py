import stripe

# Replace with your Stripe secret key
stripe.api_key = "your_stripe_secret_key"

def create_checkout_session(success_url, cancel_url, line_items):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return checkout_session.id
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return None