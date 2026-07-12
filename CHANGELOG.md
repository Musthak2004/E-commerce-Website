# Changelog

## [0.1.0.0] - 2026-07-12

### Added
- Seller dashboard — sellers can now view their products, orders, revenue, and sales stats in one place
- Product recommendations — "Frequently Bought Together" suggestions on cart and product detail pages
- Interactive star rating and button ripple microinteractions throughout the shopping experience
- Price displayed in Add to Cart button for quicker checkout decisions
- Quantity selector on cart items with stock-aware clamping
- Shipping progress bar showing remaining amount for free shipping
- Product reviews section on product detail pages with review creation flow
- Profile page with account info card, avatar preview, and account type badge
- Search keyboard shortcut (press `/` to open search), query highlighting in results, and better empty state suggestions

### Fixed
- HTMX integrity hash mismatch that was blocking all HTMX-powered features (add-to-cart, wishlist toggle, cart updates)
- Removed orphan `</style>` tag from product list template
- Search usability with result counts and improved empty state
- Mobile responsive layout issues across all pages
- Dead code and inline style inconsistencies from earlier migrations

### Changed
- Checkout flow now redirects to payment step with clearer success messaging
- Stripped fake statistics and fixed broken links for credibility
- Cart recommendations now exclude items already in the cart
- Better search results with keyboard shortcuts, highlighting, and contextual suggestions

### Removed
- Dead code and inline style artifacts from earlier CSS migration
