"""
Synthetic feedback dataset generator for ProductPulse.
Generates realistic multi-week customer feedback across multiple product areas,
customer segments, and devices.

Key scenario elements:
- Week 1 & 2: Baseline healthy operation with typical mild background noise across all areas.
- Week 3: Emerging surge in Android checkout payment failures (+78% complaints, tokenization timeouts).
  Also includes search speed feedback (ambiguous/control group) and normal iOS/web traffic.
- Week 4 (Post-intervention): Measurable drop in Android checkout failures after token retry fallback intervention,
  demonstrating clear positive outcome.
"""

from typing import List
from .schema import FeedbackItem, ProductArea, CustomerSegment


def get_all_feedback() -> List[FeedbackItem]:
    items: List[FeedbackItem] = []

    # ==========================================
    # WEEK 1: Baseline (Normal Operations)
    # ==========================================
    week1_data = [
        # Checkout / Payments (Normal baseline)
        ("fb-101", "2026-09-01", 1, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Payment went through quickly", "Smooth checkout with Google Pay on my Pixel 8.", 0.85, False),
        ("fb-102", "2026-09-02", 1, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.IOS,
         "Apple Pay works like a charm", "No issues paying for the annual subscription.", 0.90, False),
        ("fb-103", "2026-09-03", 1, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.WEB_DESKTOP,
         "Card expired message", "Got a clear prompt that my card was expired, updated easily.", 0.40, False),
        ("fb-104", "2026-09-03", 1, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Minor delay during checkout", "Took around 4 seconds to complete transaction, but succeeded.", 0.10, False),
        ("fb-105", "2026-09-04", 1, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ENTERPRISE,
         "Invoice generation fast", "Enterprise billing portal generated our monthly invoice instantly.", 0.80, False),
        ("fb-106", "2026-09-05", 1, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Card declined once", "Bank sent OTP late, retried and worked.", -0.20, True),
        ("fb-107", "2026-09-06", 1, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.IOS,
         "Receipt email arrived late", "Took 20 mins to get the receipt in my inbox.", -0.15, True),

        # Auth & Onboarding
        ("fb-108", "2026-09-02", 1, ProductArea.AUTH_ONBOARDING, CustomerSegment.IOS,
         "FaceID login is effortless", "Instant biometric login every time.", 0.95, False),
        ("fb-109", "2026-09-04", 1, ProductArea.AUTH_ONBOARDING, CustomerSegment.ANDROID,
         "Fingerprint sensor worked well", "Great onboarding experience.", 0.80, False),
        ("fb-110", "2026-09-05", 1, ProductArea.AUTH_ONBOARDING, CustomerSegment.WEB_DESKTOP,
         "SSO configuration clear", "Okta integration went smoothly for our team.", 0.75, False),
        ("fb-111", "2026-09-06", 1, ProductArea.AUTH_ONBOARDING, CustomerSegment.ANDROID,
         "Verification SMS took 2 mins", "A bit slow to receive text code.", -0.25, True),

        # Search & Discovery
        ("fb-112", "2026-09-01", 1, ProductArea.SEARCH_DISCOVERY, CustomerSegment.WEB_DESKTOP,
         "Search filters are great", "Easy to find products by category and rating.", 0.70, False),
        ("fb-113", "2026-09-03", 1, ProductArea.SEARCH_DISCOVERY, CustomerSegment.ANDROID,
         "Autocomplete suggestions relevant", "Helps me find items faster.", 0.65, False),
        ("fb-114", "2026-09-05", 1, ProductArea.SEARCH_DISCOVERY, CustomerSegment.IOS,
         "Search feels slightly sluggish on 4G", "Takes about 2-3 seconds to load product list.", -0.20, True),

        # Notifications
        ("fb-115", "2026-09-02", 1, ProductArea.NOTIFICATIONS, CustomerSegment.ANDROID,
         "Order dispatch notification on time", "Good real-time alert.", 0.80, False),
        ("fb-116", "2026-09-04", 1, ProductArea.NOTIFICATIONS, CustomerSegment.IOS,
         "Too many promotional push alerts", "I receive 3 notifications a day, please reduce.", -0.40, True),
    ]

    for fid, dt, wk, area, seg, title, body, sent, is_comp in week1_data:
        items.append(FeedbackItem(
            id=fid, date=dt, week=wk, product_area=area, segment=seg,
            title=title, body=body, sentiment_score=sent, is_complaint=is_comp
        ))

    # ==========================================
    # WEEK 2: Baseline (Normal Operations)
    # ==========================================
    week2_data = [
        # Checkout / Payments
        ("fb-201", "2026-09-08", 2, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.IOS,
         "Super simple checkout", "Paid with Apple Pay without friction.", 0.90, False),
        ("fb-202", "2026-09-09", 2, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.WEB_DESKTOP,
         "Stripe payment form is clean", "Auto-filled card details correctly.", 0.85, False),
        ("fb-203", "2026-09-10", 2, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Purchased subscription easily", "Google Play billing worked nicely.", 0.75, False),
        ("fb-204", "2026-09-11", 2, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Payment spinner took a few seconds", "Spinner spun for 5s then succeeded.", 0.05, False),
        ("fb-205", "2026-09-12", 2, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Payment failed once on 5G", "Showed error code 4001, retried and succeeded.", -0.30, True),
        ("fb-206", "2026-09-13", 2, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ENTERPRISE,
         "Purchase order processing timely", "Approved PO within an hour.", 0.80, False),
        ("fb-207", "2026-09-14", 2, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.IOS,
         "Currency conversion fee unclear", "Didn't realize currency conversion applied.", -0.25, True),

        # Auth & Onboarding
        ("fb-208", "2026-09-08", 2, ProductArea.AUTH_ONBOARDING, CustomerSegment.ANDROID,
         "App remember me works well", "I don't have to log in every time.", 0.80, False),
        ("fb-209", "2026-09-11", 2, ProductArea.AUTH_ONBOARDING, CustomerSegment.WEB_DESKTOP,
         "Password reset email delayed", "Took 5 minutes to arrive.", -0.20, True),

        # Search & Discovery (mild latency complaint - control scenario)
        ("fb-210", "2026-09-09", 2, ProductArea.SEARCH_DISCOVERY, CustomerSegment.WEB_DESKTOP,
         "Search latency a bit high in the evening", "Queries take 1.8 seconds between 8-10pm.", -0.25, True),
        ("fb-211", "2026-09-12", 2, ProductArea.SEARCH_DISCOVERY, CustomerSegment.ANDROID,
         "Search results match exact words", "Pretty accurate search.", 0.70, False),

        # Notifications
        ("fb-212", "2026-09-10", 2, ProductArea.NOTIFICATIONS, CustomerSegment.IOS,
         "Daily summary notification is helpful", "Summary digests are great.", 0.85, False),
    ]

    for fid, dt, wk, area, seg, title, body, sent, is_comp in week2_data:
        items.append(FeedbackItem(
            id=fid, date=dt, week=wk, product_area=area, segment=seg,
            title=title, body=body, sentiment_score=sent, is_complaint=is_comp
        ))

    # =========================================================================
    # WEEK 3: EMERGING SURGE IN ANDROID PAYMENT FAILURES (Dominant Problem)
    # Plus mild search complaints (Ambiguous control problem)
    # =========================================================================
    week3_data = [
        # ANDROID PAYMENT SURGE (Critical Incident)
        ("fb-301", "2026-09-15", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Payment completely failed on Android", "Cannot checkout! Keeps showing 'Payment tokenization timed out'. App version 4.12.0.", -0.90, True),
        ("fb-302", "2026-09-15", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "App crashed during payment processing", "Tapped 'Pay with Card', screen froze, then error: Gateway timeout 504.", -0.95, True),
        ("fb-303", "2026-09-16", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Unable to buy subscription on Samsung Galaxy S24", "Failed 4 times in a row. Money deducted once then reversed. Extremely frustrating!", -0.92, True),
        ("fb-304", "2026-09-16", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Payment error ERR_TOKEN_MISMATCH", "Every time I confirm checkout on Android, it fails with token exchange error.", -0.88, True),
        ("fb-305", "2026-09-16", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Checkout spinner spins endlessly", "Waited 2 minutes, order was never placed on my Pixel 7.", -0.85, True),
        ("fb-306", "2026-09-17", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Can't place order, losing customers!", "Tried to checkout business inventory from Android app. Kept rejecting valid Visa card.", -0.90, True),
        ("fb-307", "2026-09-17", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Android checkout broken after update", "Ever since app auto-updated to 4.12 yesterday, payment screen fails every single time.", -0.95, True),
        ("fb-308", "2026-09-17", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Payment failed: Handshake timeout", "The checkout dialog crashes when contacting GooglePay SDK wrapper.", -0.89, True),
        ("fb-309", "2026-09-18", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Card tokenization failed", "Message says 'Failed to tokenize payment method. Please try another card.' Other cards also fail!", -0.91, True),
        ("fb-310", "2026-09-18", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Terrible experience at checkout", "Android payment gateway is totally down. Switched to website on PC to finish order.", -0.80, True),
        ("fb-311", "2026-09-19", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Repeated payment failures", "Tried 3 different debit cards on Android, all fail with token timeout error.", -0.87, True),
        ("fb-312", "2026-09-19", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Failed payment loop", "Click Pay -> 30s loading -> 'Error processing request'. Fix this immediately!", -0.93, True),
        ("fb-313", "2026-09-20", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Order checkout rejected", "Android app throws unhandled exception during payment gateway callback.", -0.89, True),
        ("fb-314", "2026-09-20", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Checkout button does nothing or errors", "Hit checkout, spinner freezes and gives timeout error code 5002.", -0.85, True),

        # iOS / Web Payments in Week 3 (Demonstrates problem is concentrated in Android!)
        ("fb-315", "2026-09-16", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.IOS,
         "Apple Pay worked immediately", "Checkout was instant on iPhone 15 Pro.", 0.90, False),
        ("fb-316", "2026-09-18", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.WEB_DESKTOP,
         "Web checkout works fine", "Used Chrome on Windows, payment completed without any hitch.", 0.85, False),
        ("fb-317", "2026-09-19", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ENTERPRISE,
         "Enterprise wire transfer logged", "Seamless invoicing process.", 0.80, False),
        ("fb-318", "2026-09-17", 3, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.IOS,
         "Payment confirmation screen clear", "Received order ID right away.", 0.85, False),

        # Auth & Onboarding in Week 3 (Normal)
        ("fb-319", "2026-09-16", 3, ProductArea.AUTH_ONBOARDING, CustomerSegment.ANDROID,
         "Signed up with Google account", "One click Google login worked fine.", 0.85, False),
        ("fb-320", "2026-09-18", 3, ProductArea.AUTH_ONBOARDING, CustomerSegment.IOS,
         "Sign in with Apple is fast", "No issues logging in.", 0.90, False),

        # Search & Discovery (Mild latency complaints - Ambiguous control case)
        ("fb-321", "2026-09-15", 3, ProductArea.SEARCH_DISCOVERY, CustomerSegment.WEB_DESKTOP,
         "Search filtering is a bit slow", "Takes 2.1 seconds to filter by brand.", -0.30, True),
        ("fb-322", "2026-09-17", 3, ProductArea.SEARCH_DISCOVERY, CustomerSegment.ANDROID,
         "Search result loading time", "Search page could be faster on mobile data.", -0.25, True),
        ("fb-323", "2026-09-19", 3, ProductArea.SEARCH_DISCOVERY, CustomerSegment.IOS,
         "Search catalog is extensive", "Found the exact replacement part I needed.", 0.75, False),

        # Notifications in Week 3
        ("fb-324", "2026-09-17", 3, ProductArea.NOTIFICATIONS, CustomerSegment.ANDROID,
         "Push notification arrived quickly", "Alerted me when back in stock.", 0.80, False),
    ]

    for fid, dt, wk, area, seg, title, body, sent, is_comp in week3_data:
        items.append(FeedbackItem(
            id=fid, date=dt, week=wk, product_area=area, segment=seg,
            title=title, body=body, sentiment_score=sent, is_complaint=is_comp
        ))

    # =========================================================================
    # WEEK 4: POST-INTERVENTION FEEDBACK (Intervention: Android SDK retry fallback)
    # Android checkout failures plummet, demonstrating measurable success!
    # =========================================================================
    week4_data = [
        # Android Payments (RECOVERED)
        ("fb-401", "2026-09-22", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Payment now works perfectly!", "Updated to 4.12.1 patch. Checkout completed smoothly in 1 second on my Galaxy S24.", 0.95, False),
        ("fb-402", "2026-09-22", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Checkout issue fixed", "Payment previously failed earlier this week, tried again today and Google Pay worked instantly.", 0.90, False),
        ("fb-403", "2026-09-23", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Smooth transaction on Pixel 8", "Checkout was super quick, no more timeout errors.", 0.88, False),
        ("fb-404", "2026-09-23", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Card tokenized without issues", "App handled card details effortlessly. Appreciate the fast bug fix!", 0.92, False),
        ("fb-405", "2026-09-24", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Fast purchase flow", "Bought two items on Android app without any errors.", 0.85, False),
        ("fb-406", "2026-09-24", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Fallback payment worked", "Had a momentary connection blip and app retried automatically. Great resilience.", 0.82, False),
        ("fb-407", "2026-09-25", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ANDROID,
         "Card declined due to insufficient funds", "Standard bank decline, not an app error.", -0.20, True),  # Single normal complaint

        # iOS / Web Payments in Week 4 (Steady)
        ("fb-408", "2026-09-22", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.IOS,
         "Apple Pay remains great", "Fast and responsive checkout.", 0.92, False),
        ("fb-409", "2026-09-23", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.WEB_DESKTOP,
         "Desktop checkout solid", "No problems purchasing on web.", 0.85, False),
        ("fb-410", "2026-09-25", 4, ProductArea.CHECKOUT_PAYMENTS, CustomerSegment.ENTERPRISE,
         "Enterprise renewal seamless", "Automated invoice billing succeeded.", 0.90, False),

        # Auth & Onboarding in Week 4
        ("fb-411", "2026-09-23", 4, ProductArea.AUTH_ONBOARDING, CustomerSegment.ANDROID,
         "Easy setup on new tablet", "Downloaded and signed in within 30 seconds.", 0.85, False),
        ("fb-412", "2026-09-24", 4, ProductArea.AUTH_ONBOARDING, CustomerSegment.IOS,
         "Passkey login works well", "Loved the biometric passkey experience.", 0.90, False),

        # Search & Discovery in Week 4 (Ambiguous control problem - still mild latency complaints)
        ("fb-413", "2026-09-22", 4, ProductArea.SEARCH_DISCOVERY, CustomerSegment.WEB_DESKTOP,
         "Search still takes 2 seconds", "Search speed hasn't changed much, still somewhat slow on large catalog.", -0.30, True),
        ("fb-414", "2026-09-24", 4, ProductArea.SEARCH_DISCOVERY, CustomerSegment.ANDROID,
         "Search works fine", "Found products easily.", 0.70, False),

        # Notifications in Week 4
        ("fb-415", "2026-09-23", 4, ProductArea.NOTIFICATIONS, CustomerSegment.ANDROID,
         "Delivery tracking alert arrived in time", "Useful push alert.", 0.85, False),
    ]

    for fid, dt, wk, area, seg, title, body, sent, is_comp in week4_data:
        items.append(FeedbackItem(
            id=fid, date=dt, week=wk, product_area=area, segment=seg,
            title=title, body=body, sentiment_score=sent, is_complaint=is_comp
        ))

    return items
