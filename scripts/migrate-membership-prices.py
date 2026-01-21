# This script is used to move all customers to the default price of their subscribed product.

import stripe
stripe.api_key = ""

default_prices = {}
def get_default_price_for_product(product_id):
    # Use a cache to avoid lookups
    if product_id not in default_prices.keys():
        product = stripe.Product.retrieve(product_id)
        default_prices[product_id] = product.default_price

    return default_prices[product_id]

# Migrate all subscriptions to default prices for product at next billing interval.
def migrate_customers_to_default_prices(perform_update):

    subscriptions = stripe.Subscription.list(limit=3)

    numMigrations = 0

    # All active subscriptions
    for sub in subscriptions.auto_paging_iter():
        if sub.plan.active is False:
            pass # Do not migrate ending subscriptions

        # Get subscription items associated with subscription. We should only have one.
        items = stripe.SubscriptionItem.list(subscription=sub.id)

        for item in items:
            default_price = get_default_price_for_product(item.price.product)

            print('price: %r default: %r' % (item.price.id, default_price))

            if item.price.id != default_price:
                numMigrations += 1
                print('%d: Subscription %r will be updated to default price.' % (numMigrations, sub.id))

                if perform_update:
                    stripe.SubscriptionItem.modify(item.id, price=default_price, proration_behavior='none')

migrate_customers_to_default_prices(perform_update=True)