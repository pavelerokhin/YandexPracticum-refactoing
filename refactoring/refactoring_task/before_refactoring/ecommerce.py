"""
Файл ecommerce.py
Цель: показать максимально «живые» code smells для курса рефакторинга.

Присутствующие code smells:
1. Long Method (generate_report)
2. Duplicate Code (total_price, grand_total, calculate_shipping)
3. Feature Envy (DiscountHelper, ShippingCalculator)
4. Large Class (Customer)
5. Primitive Obsession (статусы как строки, типы клиентов как числа)
6. Switch Statements (можно заменить полиморфизмом)
7. Magic Numbers и дублирование констант
8. God Class тенденции (Order делает слишком много)
9. Long Parameter List
10. Data Class (Product)
"""

# Константы, но некоторые будут дублированы в коде 🙃
TAX_RATE = 0.20
LOYALTY_DISCOUNT = 0.05
FREE_SHIPPING_THRESHOLD = 100.0
PREMIUM_CUSTOMER_TYPE = 1
GOLD_CUSTOMER_TYPE = 2
REGULAR_CUSTOMER_TYPE = 0


# ――― Data Class (только данные, нет поведения) ―――
class Product:
    def __init__(self, name: str, price: float, category: str, weight: float):
        self.name = name
        self.price = price
        self.category = category  # строка вместо enum - Primitive Obsession
        self.weight = weight


# ――― Large Class - слишком много ответственности ―――
class Customer:
    """
    Делает всё: хранит данные, валидирует, форматирует, считает скидки...
    """
    def __init__(self, customer_id: int, name: str, email: str,
                 customer_type: int, total_spent: float, orders_count: int):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.customer_type = customer_type  # Primitive Obsession - число вместо enum
        self.total_spent = total_spent
        self.orders_count = orders_count
        self.address = ""
        self.phone = ""
        self.registration_date = None
        self.last_login = None
        self.preferences = {}

    # Validation logic - не по SRP
    def is_valid_email(self):
        return "@" in self.email and "." in self.email

    def is_valid_phone(self):
        return len(self.phone.replace("-", "").replace(" ", "")) >= 10

    # Formatting logic - не по SRP
    def get_display_name(self):
        if self.customer_type == 2:  # Magic Number
            return f"🥇 {self.name}"
        elif self.customer_type == 1:  # Magic Number
            return f"⭐ {self.name}"
        else:
            return self.name

    # Business logic - не по SRP
    def get_loyalty_multiplier(self):
        if self.customer_type == 2:  # Gold - Magic Number
            return 0.15
        elif self.customer_type == 1:  # Premium - Magic Number
            return 0.10
        else:
            return 0.05

    def can_get_free_shipping(self):
        return self.customer_type >= 1  # Magic Number

    # Data access logic - не по SRP
    def update_spent_amount(self, amount: float):
        self.total_spent += amount
        self.orders_count += 1


# ――― God Class тенденции - Order делает слишком много ―――
class Order:
    def __init__(self, customer_id: int):
        self.customer_id = customer_id
        self.items: list[Product] = []
        self.status = "OPEN"  # Primitive Obsession - строка вместо enum
        self.shipping_address = ""
        self.notes = ""
        self.created_at = None
        self.updated_at = None

    def add_item(self, product: Product, quantity: int = 1):
        # Примитивная реализация - не учитывает quantity правильно
        for _ in range(quantity):
            self.items.append(product)

    # ――― Duplicate Code №1 ―――
    def total_price(self):
        total = 0
        for p in self.items:
            total += p.price
        return total

    # ――― Duplicate Code №2 (та же логика, другая реализация) ―――
    def grand_total(self):
        s = 0
        for p in self.items:
            s += p.price
        return s

    # ――― Duplicate Code №3 (похожая логика подсчёта) ―――
    def calculate_shipping(self):
        total_weight = 0
        for p in self.items:
            total_weight += p.weight

        base_price = 0
        for p in self.items:  # Опять итерируемся по items
            base_price += p.price

        if base_price > 100:  # Magic Number вместо FREE_SHIPPING_THRESHOLD
            return 0
        elif total_weight < 1:
            return 5.99  # Magic Number
        elif total_weight < 5:
            return 9.99  # Magic Number
        else:
            return 15.99  # Magic Number

    # Switch Statement - можно заменить полиморфизмом
    def get_status_display(self):
        if self.status == "OPEN":
            return "📝 Open"
        elif self.status == "PROCESSING":
            return "⚙️ Processing"
        elif self.status == "SHIPPED":
            return "🚚 Shipped"
        elif self.status == "DELIVERED":
            return "✅ Delivered"
        elif self.status == "CANCELLED":
            return "❌ Cancelled"
        else:
            return "❓ Unknown"

    def can_be_cancelled(self):
        return self.status in ["OPEN", "PROCESSING"]

    def can_be_modified(self):
        return self.status == "OPEN"


# ――― Feature Envy - лезет в чужие данные ―――
class DiscountHelper:
    """
    Должен считать скидки, но постоянно лезет во внутренности других классов.
    """
    def calc_loyalty_discount(self, order: Order, customer: Customer) -> float:
        # Тянет данные из order и customer вместо получения готовых значий
        num_items = len(order.items)
        base_price = order.total_price()
        customer_multiplier = customer.get_loyalty_multiplier()

        # Дублируется логика из Customer
        if customer.customer_type == 2:  # Magic Number
            minimum_items = 1
        elif customer.customer_type == 1:  # Magic Number
            minimum_items = 2
        else:
            minimum_items = 3

        return base_price * customer_multiplier if num_items >= minimum_items else 0.0

    def calc_bulk_discount(self, order: Order) -> float:
        # Feature Envy - опять лезет в order.items
        category_counts = {}
        for item in order.items:
            if item.category not in category_counts:
                category_counts[item.category] = 0
            category_counts[item.category] += 1

        discount = 0
        for category, count in category_counts.items():
            if count >= 5:  # Magic Number
                discount += count * 2.5  # Magic Number
        return discount


# ――― Ещё один Feature Envy ―――
class ShippingCalculator:
    def calculate_advanced_shipping(self, order: Order, customer: Customer) -> float:
        # Дублирует логику из Order.calculate_shipping но с другими правилами
        total_weight = 0
        for p in order.items:
            total_weight += p.weight

        base_price = 0
        for p in order.items:
            base_price += p.price

        # Feature Envy - использует internal knowledge о customer
        if customer.can_get_free_shipping() and base_price > 50:  # Magic Number
            return 0

        if customer.customer_type == 2:  # Magic Number
            return max(0, total_weight * 1.5 - 5)  # Magic Number
        elif customer.customer_type == 1:  # Magic Number
            return total_weight * 2.0  # Magic Number
        else:
            return total_weight * 2.5 + 3.99  # Magic Numbers


# ――― Long Method + множественные нарушения SRP ―――
class Analytics:
    def generate_comprehensive_report(self, orders: list[Order], customers: dict[int, Customer]) -> dict:
        """
        100+ строк монстр-метод, который делает ВСЁ:
        - агрегацию данных
        - сложные вычисления
        - логирование
        - форматирование
        - вывод на экран
        - валидацию
        - сортировку
        """
        # Long Parameter List было бы ещё хуже, но пока обойдёмся
        report = {
            "total_orders": len(orders),
            "total_revenue_net": 0.0,
            "total_revenue_gross": 0.0,
            "total_shipping": 0.0,
            "total_discounts": 0.0,
            "top_customers": {},
            "avg_items_per_order": 0.0,
            "categories_stats": {},
            "customer_segments": {"gold": 0, "premium": 0, "regular": 0},
            "shipping_analysis": {},
            "debug_log": [],
            "warnings": []
        }

        total_items = 0
        discount_helper = DiscountHelper()
        shipping_calc = ShippingCalculator()

        # ――― Блок 1: основная агрегация (слишком много в одном месте) ―――
        for order in orders:
            # Duplicate Code - та же логика подсчёта, что в Order
            net_price = 0
            for item in order.items:
                net_price += item.price

            tax_amount = net_price * 0.2  # Magic Number дублирует TAX_RATE
            gross_price = net_price + tax_amount

            report["total_revenue_net"] += net_price
            report["total_revenue_gross"] += gross_price
            total_items += len(order.items)

            # ――― Блок 2: анализ доставки ―――
            customer = customers.get(order.customer_id)
            if customer:
                shipping_cost = shipping_calc.calculate_advanced_shipping(order, customer)
                report["total_shipping"] += shipping_cost

                # Customer segmentation с Magic Numbers
                if customer.customer_type == 2:
                    report["customer_segments"]["gold"] += 1
                elif customer.customer_type == 1:
                    report["customer_segments"]["premium"] += 1
                else:
                    report["customer_segments"]["regular"] += 1

            # ――― Блок 3: топ клиенты (можно было бы вынести) ―――
            cid = order.customer_id
            if cid not in report["top_customers"]:
                report["top_customers"][cid] = {
                    "revenue": 0,
                    "orders": 0,
                    "avg_order": 0
                }
            report["top_customers"][cid]["revenue"] += gross_price
            report["top_customers"][cid]["orders"] += 1

            # ――― Блок 4: анализ категорий товаров ―――
            for item in order.items:
                cat = item.category
                if cat not in report["categories_stats"]:
                    report["categories_stats"][cat] = {
                        "count": 0,
                        "revenue": 0,
                        "avg_price": 0
                    }
                report["categories_stats"][cat]["count"] += 1
                report["categories_stats"][cat]["revenue"] += item.price

            # ――― Блок 5: скидки и детальное логирование ―――
            if customer:
                loyalty_discount = discount_helper.calc_loyalty_discount(order, customer)
                bulk_discount = discount_helper.calc_bulk_discount(order)
                total_discount = loyalty_discount + bulk_discount
                report["total_discounts"] += total_discount

                # Подробное логирование (не нужно в production)
                log_entry = (
                    f"[Customer: {customer.name}] "
                    f"Order: {len(order.items)} items, "
                    f"Net: €{net_price:.2f}, "
                    f"Gross: €{gross_price:.2f}, "
                    f"Shipping: €{shipping_cost:.2f}, "
                    f"Discount: €{total_discount:.2f}, "
                    f"Status: {order.status}"
                )
                report["debug_log"].append(log_entry)

                # Валидация данных клиента (не место для этого здесь)
                if not customer.is_valid_email():
                    report["warnings"].append(f"Invalid email for customer {customer.name}")
                if not customer.is_valid_phone():
                    report["warnings"].append(f"Invalid phone for customer {customer.name}")

        # ――― Блок 6: пост-обработка и вычисления ―――
        if orders:
            report["avg_items_per_order"] = round(total_items / len(orders), 2)

        # Досчитываем средние цены по категориям
        for cat_stats in report["categories_stats"].values():
            if cat_stats["count"] > 0:
                cat_stats["avg_price"] = round(
                    cat_stats["revenue"] / cat_stats["count"], 2
                )

        # Досчитываем средний чек по клиентам
        for customer_stats in report["top_customers"].values():
            if customer_stats["orders"] > 0:
                customer_stats["avg_order"] = round(
                    customer_stats["revenue"] / customer_stats["orders"], 2
                )

        # ――― Блок 7: сортировки (много кода для простой задачи) ―――
        # Сортируем топ клиентов по выручке
        report["top_customers"] = dict(
            sorted(
                report["top_customers"].items(),
                key=lambda kv: kv[1]["revenue"],
                reverse=True
            )
        )

        # Сортируем категории по популярности
        report["categories_stats"] = dict(
            sorted(
                report["categories_stats"].items(),
                key=lambda kv: kv[1]["count"],
                reverse=True
            )
        )

        # ――― Блок 8: форматированный вывод (нарушение SRP) ―――
        print("=" * 50)
        print("📊 COMPREHENSIVE E-COMMERCE REPORT")
        print("=" * 50)
        print(f"📦 Total Orders: {report['total_orders']}")
        print(f"💰 Revenue (Net): €{report['total_revenue_net']:.2f}")
        print(f"💰 Revenue (Gross): €{report['total_revenue_gross']:.2f}")
        print(f"🚚 Shipping Revenue: €{report['total_shipping']:.2f}")
        print(f"🎁 Discounts Given: €{report['total_discounts']:.2f}")
        print(f"📈 Avg Items/Order: {report['avg_items_per_order']}")

        print("\n🏆 TOP CUSTOMERS (by revenue):")
        for i, (cid, stats) in enumerate(list(report["top_customers"].items())[:5]):
            customer_name = customers[cid].get_display_name() if cid in customers else f"Customer {cid}"
            print(f"  {i+1}. {customer_name}: €{stats['revenue']:.2f} ({stats['orders']} orders)")

        print("\n📊 CATEGORY PERFORMANCE:")
        for cat, stats in list(report["categories_stats"].items())[:5]:
            print(f"  {cat}: {stats['count']} items, €{stats['revenue']:.2f} revenue")

        print(f"\n👥 CUSTOMER SEGMENTS:")
        print(f"  🥇 Gold: {report['customer_segments']['gold']}")
        print(f"  ⭐ Premium: {report['customer_segments']['premium']}")
        print(f"  👤 Regular: {report['customer_segments']['regular']}")

        if report["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
            for warning in report["warnings"][:3]:  # Показываем только первые 3
                print(f"  - {warning}")

        print("=" * 50)

        return report


# ――― Primitive Obsession пример ―――
class OrderProcessor:
    """
    Работает с примитивными типами вместо объектов-значений
    """
    def process_payment(self, amount: float, currency: str, payment_method: str,
                       card_number: str, expiry: str, cvv: str) -> bool:
        # Long Parameter List + всё примитивные типы
        # Должны были бы быть Money, PaymentMethod, CreditCard objects

        if currency == "EUR":  # Switch statement
            tax_rate = 0.20
        elif currency == "USD":
            tax_rate = 0.08
        elif currency == "GBP":
            tax_rate = 0.18
        else:
            return False

        if payment_method == "CREDIT":  # ещё один switch
            fee = amount * 0.029  # Magic Number
        elif payment_method == "DEBIT":
            fee = amount * 0.019  # Magic Number
        elif payment_method == "PAYPAL":
            fee = amount * 0.034 + 0.30  # Magic Numbers
        else:
            return False

        # Примитивная валидация строк вместо объектов
        if len(card_number.replace(" ", "")) != 16:
            return False
        if len(cvv) not in [3, 4]:
            return False

        return True


# ――― Тестовые данные для демонстрации ―――
if __name__ == "__main__":
    # Создаём продукты
    book = Product("Python Programming", 45.99, "books", 0.5)
    laptop = Product("Gaming Laptop", 899.99, "electronics", 2.1)
    pen = Product("Premium Pen", 12.99, "office", 0.1)
    backpack = Product("Travel Backpack", 79.99, "accessories", 0.8)

    # Создаём клиентов разных типов
    customers = {
        101: Customer(101, "Alice Johnson", "alice@email.com", GOLD_CUSTOMER_TYPE, 1500.0, 12),
        102: Customer(102, "Bob Smith", "bob@email.com", PREMIUM_CUSTOMER_TYPE, 800.0, 6),
        103: Customer(103, "Carol Davis", "carol@invalid-email", REGULAR_CUSTOMER_TYPE, 150.0, 2)
    }

    # Создаём заказы
    order1 = Order(101)
    order1.add_item(laptop, 1)
    order1.add_item(backpack, 1)
    order1.status = "DELIVERED"

    order2 = Order(102)
    order2.add_item(book, 2)
    order2.add_item(pen, 3)
    order2.status = "SHIPPED"

    order3 = Order(103)
    order3.add_item(pen, 1)
    order3.status = "PROCESSING"

    order4 = Order(101)  # Alice делает ещё один заказ
    order4.add_item(book, 5)  # bulk purchase
    order4.status = "OPEN"

    # Запускаем анализ
    analytics = Analytics()
    report = analytics.generate_comprehensive_report([order1, order2, order3, order4], customers)

    print(f"\nGenerated {len(report['debug_log'])} debug entries")
    print(f"Found {len(report['warnings'])} data quality issues")