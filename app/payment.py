from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Subscription
import stripe
import os
from datetime import datetime, timedelta

payment_bp = Blueprint('payment', __name__)

# Initialize Stripe with the API key from environment variable
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Dictionary of plan IDs and their details
PLANS = {
    'basic': {
        'name': 'Basic Plan',
        'price_id': os.environ.get('STRIPE_BASIC_PRICE_ID', 'price_placeholder_basic'),
        'amount': 900,  # $9.00
        'blog_limit': 5,
        'features': ['Basic SEO optimization', 'Standard cover images']
    },
    'pro': {
        'name': 'Pro Plan',
        'price_id': os.environ.get('STRIPE_PRO_PRICE_ID', 'price_placeholder_pro'),
        'amount': 1900,  # $19.00
        'blog_limit': 15,
        'features': ['Advanced SEO optimization', 'Premium cover images', 'Custom writing style']
    },
    'enterprise': {
        'name': 'Enterprise Plan',
        'price_id': os.environ.get('STRIPE_ENTERPRISE_PRICE_ID', 'price_placeholder_enterprise'),
        'amount': 4900,  # $49.00
        'blog_limit': None,  # Unlimited
        'features': ['Advanced SEO optimization', 'Premium cover images', 'Custom writing style', 'Priority support']
    }
}

@payment_bp.route('/plans')
def plans():
    """Show available subscription plans"""
    return render_template('plans.html', plans=PLANS)

@payment_bp.route('/subscribe/<plan_id>')
@login_required
def subscribe(plan_id):
    """Create a checkout session for the specified plan"""
    if plan_id not in PLANS:
        flash('Invalid plan selected.', 'danger')
        return redirect(url_for('payment.plans'))
    
    plan = PLANS[plan_id]
    
    try:
        # Create a Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': plan['price_id'],
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=url_for('payment.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment.cancel', _external=True),
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
            metadata={
                'plan_id': plan_id
            }
        )
        
        return redirect(checkout_session.url, code=303)
    
    except Exception as e:
        flash(f'Error creating checkout session: {str(e)}', 'danger')
        return redirect(url_for('payment.plans'))

@payment_bp.route('/success')
@login_required
def success():
    """Handle successful checkout"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return redirect(url_for('main.index'))
    
    try:
        # Retrieve checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Get subscription details
        subscription = stripe.Subscription.retrieve(checkout_session.subscription)
        
        # Get plan ID from metadata
        plan_id = checkout_session.metadata.get('plan_id')
        
        if not plan_id or plan_id not in PLANS:
            flash('Invalid plan information.', 'danger')
            return redirect(url_for('main.index'))
        
        # Update user subscription in our database
        user_subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        
        if user_subscription:
            # Update existing subscription
            user_subscription.stripe_subscription_id = subscription.id
            user_subscription.stripe_customer_id = subscription.customer
            user_subscription.plan_id = plan_id
            user_subscription.status = subscription.status
            user_subscription.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        else:
            # Create new subscription
            user_subscription = Subscription(
                user_id=current_user.id,
                stripe_subscription_id=subscription.id,
                stripe_customer_id=subscription.customer,
                plan_id=plan_id,
                status=subscription.status,
                current_period_end=datetime.fromtimestamp(subscription.current_period_end)
            )
            db.session.add(user_subscription)
        
        db.session.commit()
        
        flash(f'Successfully subscribed to {PLANS[plan_id]["name"]}!', 'success')
        return redirect(url_for('main.index'))
    
    except Exception as e:
        flash(f'Error processing subscription: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@payment_bp.route('/cancel')
@login_required
def cancel():
    """Handle canceled checkout"""
    flash('Subscription process was canceled.', 'info')
    return redirect(url_for('payment.plans'))

@payment_bp.route('/manage')
@login_required
def manage():
    """Show subscription management page"""
    # Get user's current subscription
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        flash('You don\'t have an active subscription.', 'info')
        return redirect(url_for('payment.plans'))
    
    try:
        # Get up-to-date subscription details from Stripe
        stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        
        # Calculate remaining blog posts
        if subscription.plan_id in PLANS:
            blog_limit = PLANS[subscription.plan_id]['blog_limit']
            if blog_limit is None:
                remaining_posts = "Unlimited"
            else:
                # For demo purposes, reset count each month
                # In a real app, you'd count actual blog posts created this period
                used_posts = current_user.blog_posts.count() % blog_limit
                remaining_posts = blog_limit - used_posts
        else:
            remaining_posts = "Unknown"
        
        return render_template(
            'manage_subscription.html',
            subscription=subscription,
            stripe_subscription=stripe_subscription,
            plan=PLANS.get(subscription.plan_id),
            remaining_posts=remaining_posts
        )
    
    except Exception as e:
        flash(f'Error retrieving subscription details: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@payment_bp.route('/portal')
@login_required
def portal():
    """Redirect to Stripe Customer Portal"""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_customer_id:
        flash('No subscription information found.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Create a portal session
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=url_for('payment.manage', _external=True),
        )
        
        # Redirect to the portal
        return redirect(session.url, code=303)
    
    except Exception as e:
        flash(f'Error accessing billing portal: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events for subscription updates"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        return jsonify({'status': 'error', 'message': 'Webhook secret not configured'}), 500
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_deleted(event['data']['object'])
    elif event['type'] == 'checkout.session.completed':
        handle_checkout_completed(event['data']['object'])
    
    return jsonify({'status': 'success'})

def handle_subscription_updated(subscription_object):
    """Handle subscription updated event"""
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_object.id).first()
    
    if subscription:
        subscription.status = subscription_object.status
        subscription.current_period_end = datetime.fromtimestamp(subscription_object.current_period_end)
        db.session.commit()

def handle_subscription_deleted(subscription_object):
    """Handle subscription deleted event"""
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_object.id).first()
    
    if subscription:
        subscription.status = 'canceled'
        db.session.commit()

def handle_checkout_completed(checkout_object):
    """Handle checkout completed event"""
    # This is a backup for the success route
    if checkout_object.mode == 'subscription' and checkout_object.payment_status == 'paid':
        # Get user ID from client_reference_id
        user_id = int(checkout_object.client_reference_id)
        plan_id = checkout_object.metadata.get('plan_id')
        
        if not plan_id or plan_id not in PLANS:
            return
        
        # Update subscription in database
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        
        # Get subscription details from Stripe
        stripe_subscription = stripe.Subscription.retrieve(checkout_object.subscription)
        
        if subscription:
            # Update existing subscription
            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.stripe_customer_id = stripe_subscription.customer
            subscription.plan_id = plan_id
            subscription.status = stripe_subscription.status
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=stripe_subscription.customer,
                plan_id=plan_id,
                status=stripe_subscription.status,
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end)
            )
            db.session.add(subscription)
        
        db.session.commit() 