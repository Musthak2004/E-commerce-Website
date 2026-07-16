# Changelog

## [0.2.0.0] - 2026-07-16

### Added
- Live Chat Messenger — Phase 1 (HTMX polling) allowing buyers and sellers to communicate in real-time
- Conversation model (buyer/seller FKs with SET_NULL for data preservation, product-scoped, UniqueConstraints)
- Message model (TextField max 2000 chars, sender FK SET_NULL, is_read, composite index)
- Inbox view with Subquery-annotated last message preview, unread count, and pagination (25/page)
- Conversation detail view with last-50 messages, read-marking on load, and send form
- HTMX polling endpoint (GET-only, 3s interval, `[lastRequestCompleted]` guard, sender-exclusion, 50 cap)
- POST-based mark-read endpoint separated from polling (replaces GET-write side-effect)
- Older-messages pagination endpoint with `X-Has-More` sentinel
- MessageForm with client+server validation (empty rejection, 2000 char limit, XSS auto-escaped)
- Cache-based rate limiting on send (30 messages/min/user, D24)
- Read-only Django admin for Conversation and Message with full list_display
- `touch_conversation_on_message` signal to invalidate cachalot cache on new message (D16)
- `reassign_conversation_seller` signal to sync Conversation.seller when Product.seller changes (D23)
- Chat CSS (`static/css/chat.css`) — inbox list, message bubbles (chat style), send form, responsive
- Templates: `inbox.html` (empty state, pagination), `conversation.html` (poll, send, load-older), 3 partials
- Null-safe template rendering for deleted users (D14) and deleted products (D15)
- "Messages" nav link with `fa-comment` icon and unread badge in header-right and mobile nav
- "Chat with Seller" button on product detail page with auth/ownership guards
- Chat context processor for unread count badge across all pages
- 71 unit tests across 5 test files (models, views, auth, polling, edge cases)
- 28 engineering review findings all resolved pre-implementation (security, data integrity, perf, UX)

### Fixed
- Model: buyer/seller FK on_delete changed from CASCADE to SET_NULL to preserve surviving participant's history
- Conversation model: added `updated_at` field (auto_now) for cachalot cache invalidation
- Admin: read-only permissions for staff users (was full CRUD)
- Poll endpoint: separated read-marking into POST endpoint (D20, HTTP semantics compliance)

### Changed
- Version bumped to 0.2.0.0

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
