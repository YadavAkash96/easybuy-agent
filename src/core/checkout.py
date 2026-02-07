"""Simulated checkout orchestration."""

from collections import defaultdict

from src.core.types import Address, Cart, CheckoutPlan, CheckoutStep, Payment


def build_checkout_plan(cart: Cart, address: Address, payment: Payment) -> CheckoutPlan:
    grouped: dict[str, list[str]] = defaultdict(list)

    for item in cart.items:
        grouped[item.product.retailer].append(item.product.name)

    steps: list[CheckoutStep] = []
    for retailer, product_names in grouped.items():
        steps.append(
            CheckoutStep(
                retailer=retailer,
                steps=[
                    "Open checkout",
                    f"Autofill address: {address.line1}, {address.city}",
                    f"Autofill payment: ****{payment.card_last4}",
                    f"Submit order for {', '.join(product_names)}",
                ],
            )
        )

    return CheckoutPlan(retailer_steps=steps, summary="ok")
