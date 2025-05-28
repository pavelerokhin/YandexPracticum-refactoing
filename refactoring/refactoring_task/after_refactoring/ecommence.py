"""
ecommerce_refactored.py
Результат рефакторинга: устранены code smells, применены принципы SOLID,
введены паттерны проектирования и value objects.

Исправленные code smells:
✅ Long Method → Extract Method, Extract Class
✅ Duplicate Code → Extract Method, DRY principle
✅ Feature Envy → Move Method, proper encapsulation
✅ Large Class → Extract Class, Single Responsibility
✅ Primitive Obsession → Value Objects, Enums
✅ Switch Statements → Strategy Pattern, Polymorphism
✅ Magic Numbers → Named Constants
✅ God Class → Separation of Concerns
✅ Long Parameter List → Parameter Objects
✅ Data Class → Rich Domain Objects
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from decimal import Decimal
import math


# ――― Constants (вместо magic numbers) ―――
class TaxRates:
    EUR = Decimal('0.20')
    USD = Decimal('0.08')
    GBP = Decimal('0.18')


class ShippingConstants:
    FREE_SHIPPING_THRESHOLD = Decimal('100.00')
    LIGHT_PACKAGE_THRESHOLD = Decimal('1.0')
    MEDIUM_PACKAGE_THRESHOLD = Decimal('5.0')
    LIGHT_SHIPPING_COST = Decimal('5.99')
    MEDIUM_SHIPPING_COST = Decimal('9.99')
    HEAVY_SHIPPING_COST = Decimal('15.99')


class DiscountConstants:
    LOYALTY_BASE_RATE = Decimal('0.05')
    BULK_DISCOUNT_PER_ITEM = Decimal('2.50')
    BULK_DISCOUNT_THRESHOLD = 5


# ――― Value Objects (решение Primitive Obsession) ―――
@dataclass(frozen=True)
class Money:
    """Value object для денежных сумм"""
    amount: Decimal
    currency: str = "EUR"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, multiplier: Decimal) -> 'Money':
        return Money(self.amount * multiplier, self.currency)

    def __str__(self) -> str:
        return f"€{self.amount:.2f}" if self.currency == "EUR" else f"{self.amount:.2f} {self.currency}"


@dataclass(frozen=True)
class Weight:
    """Value object для веса"""
    kilograms: Decimal

    def __post_init__(self):
        if self.kilograms < 0:
            raise ValueError("Weight cannot be negative")

    def __add__(self, other: 'Weight') -> 'Weight':
        return Weight(self.kilograms + other.kilograms)

    def is_light(self) -> bool:
        return self.kilograms < ShippingConstants.LIGHT_PACKAGE_THRESHOLD

    def is_medium(self) -> bool:
        return self.kilograms < ShippingConstants.MEDIUM_PACKAGE_THRESHOLD


# ――― Enums (вместо string/int constants) ―――
class OrderStatus(Enum):
    OPEN = "OPEN"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

    def display_name(self) -> str:
        display_map = {
            OrderStatus.OPEN: "📝 Open",
            OrderStatus.PROCESSING: "⚙️ Processing",
            OrderStatus.SHIPPED: "🚚 Shipped",
            OrderStatus.DELIVERED: "✅ Delivered",
            OrderStatus.CANCELLED: "❌ Cancelled"
        }
        return display_map.get(self, "❓ Unknown")

    def can_be_cancelled(self) -> bool:
        return self in [OrderStatus.OPEN, OrderStatus.PROCESSING]

    def can_be_modified(self) -> bool:
        return self == OrderStatus.OPEN


class CustomerType(Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    GOLD = "GOLD"

    def display_prefix(self) -> str:
        prefixes = {
            CustomerType.REGULAR: "👤 ",
            CustomerType.PREMIUM: "⭐ ",
            CustomerType.GOLD: "🥇 "
        }
        return prefixes[self]

    def loyalty_multiplier(self) -> Decimal:
        multipliers = {
            CustomerType.REGULAR: Decimal('0.05'),
            CustomerType.PREMIUM: Decimal('0.10'),
            CustomerType.GOLD: Decimal('0.15')
        }
        return multipliers[self]

    def min_items_for_loyalty(self) -> int:
        minimums = {
            CustomerType.REGULAR: 3,
            CustomerType.PREMIUM: 2,
            CustomerType.GOLD: 1
        }
        return minimums[self]

    def has_free_shipping_privilege(self) -> bool:
        return self in [CustomerType.PREMIUM, CustomerType.GOLD]


class ProductCategory(Enum):
    BOOKS = "books"
    ELECTRONICS = "electronics"
    OFFICE = "office"
    ACCESSORIES = "accessories"
    LUXURY = "luxury"


class PaymentMethod(Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    PAYPAL = "PAYPAL"

    def processing_fee_rate(self) -> Decimal:
        rates = {
            PaymentMethod.CREDIT: Decimal('0.029'),
            PaymentMethod.DEBIT: Decimal('0.019'),
            PaymentMethod.PAYPAL: Decimal('0.034')
        }
        return rates[self]

    def fixed_fee(self) -> Decimal:
        fees = {
            PaymentMethod.CREDIT: Decimal('0.00'),
            PaymentMethod.DEBIT: Decimal('0.00'),
            PaymentMethod.PAYPAL: Decimal('0.30')
        }
        return fees[self]


# ――― Rich Domain Objects (вместо Data Classes) ―――
class Product:
    """Rich domain object с поведением"""

    def __init__(self, name: str, price: Money, category: ProductCategory, weight: Weight):
        self.name = name
        self.price = price
        self.category = category
        self.weight = weight

    def is_expensive(self) -> bool:
        return self.price.amount > Decimal('100')

    def is_heavy(self) -> bool:
        return not self.weight.is_light()

    def calculate_tax(self, tax_rate: Decimal) -> Money:
        return self.price * tax_rate


@dataclass
class OrderItem:
    """Represents a product with quantity in an order"""
    product: Product
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

    def total_price(self) -> Money:
        return self.product.price * Decimal(str(self.quantity))

    def total_weight(self) -> Weight:
        return Weight(self.product.weight.kilograms * Decimal(str(self.quantity)))


# ――― Validation Services (извлечено из Large Class) ―――
class CustomerValidator:
    """Отвечает только за валидацию данных клиента"""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        return "@" in email and "." in email

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        cleaned = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        return len(cleaned) >= 10 and cleaned.isdigit()


class CustomerFormatter:
    """Отвечает только за форматирование отображения клиента"""

    @staticmethod
    def format_display_name(name: str, customer_type: CustomerType) -> str:
        return f"{customer_type.display_prefix()}{name}"


# ――― Customer (разбили Large Class) ―――
class Customer:
    """Сфокусированный класс клиента без множественных ответственностей"""

    def __init__(self, customer_id: int, name: str, email: str, customer_type: CustomerType,
                 total_spent: Money, orders_count: int):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.customer_type = customer_type
        self.total_spent = total_spent
        self.orders_count = orders_count
        self.address = ""
        self.phone = ""

    def get_display_name(self) -> str:
        return CustomerFormatter.format_display_name(self.name, self.customer_type)

    def is_valid_email(self) -> bool:
        return CustomerValidator.is_valid_email(self.email)

    def is_valid_phone(self) -> bool:
        return CustomerValidator.is_valid_phone(self.phone)

    def update_purchase_history(self, amount: Money) -> None:
        self.total_spent += amount
        self.orders_count += 1

    def qualifies_for_loyalty_discount(self, item_count: int) -> bool:
        return item_count >= self.customer_type.min_items_for_loyalty()

    def can_get_free_shipping(self) -> bool:
        return self.customer_type.has_free_shipping_privilege()


# ――― Order Calculator (извлечено из God Class) ―――
class OrderCalculator:
    """Отвечает только за расчёты по заказу"""

    @staticmethod
    def calculate_total_price(items: List[OrderItem]) -> Money:
        if not items:
            return Money(Decimal('0'))

        total = items[0].total_price()
        for item in items[1:]:
            total += item.total_price()
        return total

    @staticmethod
    def calculate_total_weight(items: List[OrderItem]) -> Weight:
        total_kg = Decimal('0')
        for item in items:
            total_kg += item.total_weight().kilograms
        return Weight(total_kg)

    @staticmethod
    def count_items_by_category(items: List[OrderItem]) -> Dict[ProductCategory, int]:
        counts = {}
        for item in items:
            category = item.product.category
            counts[category] = counts.get(category, 0) + item.quantity
        return counts


# ――― Strategy Pattern для скидок ―――
class DiscountStrategy(ABC):
    """Абстрактная стратегия для расчёта скидок"""

    @abstractmethod
    def calculate_discount(self, order_total: Money, items: List[OrderItem],
                           customer: Customer) -> Money:
        pass


class LoyaltyDiscountStrategy(DiscountStrategy):
    """Стратегия скидки за лояльность"""

    def calculate_discount(self, order_total: Money, items: List[OrderItem],
                           customer: Customer) -> Money:
        total_items = sum(item.quantity for item in items)

        if customer.qualifies_for_loyalty_discount(total_items):
            discount_rate = customer.customer_type.loyalty_multiplier()
            return order_total * discount_rate

        return Money(Decimal('0'))


class BulkDiscountStrategy(DiscountStrategy):
    """Стратегия скидки за оптовые покупки"""

    def calculate_discount(self, order_total: Money, items: List[OrderItem],
                           customer: Customer) -> Money:
        category_counts = OrderCalculator.count_items_by_category(items)

        total_discount = Decimal('0')
        for category, count in category_counts.items():
            if count >= DiscountConstants.BULK_DISCOUNT_THRESHOLD:
                total_discount += Decimal(str(count)) * DiscountConstants.BULK_DISCOUNT_PER_ITEM

        return Money(total_discount)


class DiscountCalculator:
    """Использует стратегии для расчёта скидок"""

    def __init__(self):
        self.strategies = [
            LoyaltyDiscountStrategy(),
            BulkDiscountStrategy()
        ]

    def calculate_total_discount(self, order_total: Money, items: List[OrderItem],
                                 customer: Customer) -> Money:
        total_discount = Money(Decimal('0'))

        for strategy in self.strategies:
            discount = strategy.calculate_discount(order_total, items, customer)
            total_discount += discount

        return total_discount


# ――― Strategy Pattern для доставки ―――
class ShippingStrategy(ABC):
    """Абстрактная стратегия для расчёта доставки"""

    @abstractmethod
    def calculate_shipping(self, order_total: Money, total_weight: Weight,
                           customer: Customer) -> Money:
        pass


class StandardShippingStrategy(ShippingStrategy):
    """Стандартная стратегия доставки"""

    def calculate_shipping(self, order_total: Money, total_weight: Weight,
                           customer: Customer) -> Money:
        # Бесплатная доставка для крупных заказов
        if order_total.amount >= ShippingConstants.FREE_SHIPPING_THRESHOLD:
            return Money(Decimal('0'))

        # Расчёт по весу
        if total_weight.is_light():
            return Money(ShippingConstants.LIGHT_SHIPPING_COST)
        elif total_weight.is_medium():
            return Money(ShippingConstants.MEDIUM_SHIPPING_COST)
        else:
            return Money(ShippingConstants.HEAVY_SHIPPING_COST)


class PremiumShippingStrategy(ShippingStrategy):
    """Премиум стратегия доставки с льготами"""

    def calculate_shipping(self, order_total: Money, total_weight: Weight,
                           customer: Customer) -> Money:
        # Бесплатная доставка для премиум клиентов при меньшей сумме
        if (customer.can_get_free_shipping() and
                order_total.amount >= Decimal('50')):
            return Money(Decimal('0'))

        # Льготные тарифы по типу клиента
        rate_per_kg = self._get_rate_for_customer_type(customer.customer_type)
        base_cost = total_weight.kilograms * rate_per_kg

        # Скидка для Gold клиентов
        if customer.customer_type == CustomerType.GOLD:
            base_cost = max(Decimal('0'), base_cost - Decimal('5'))

        return Money(base_cost)

    def _get_rate_for_customer_type(self, customer_type: CustomerType) -> Decimal:
        rates = {
            CustomerType.REGULAR: Decimal('2.50'),
            CustomerType.PREMIUM: Decimal('2.00'),
            CustomerType.GOLD: Decimal('1.50')
        }
        return rates[customer_type]


class ShippingCalculator:
    """Использует стратегии для расчёта доставки"""

    def __init__(self):
        self.standard_strategy = StandardShippingStrategy()
        self.premium_strategy = PremiumShippingStrategy()

    def calculate_shipping(self, order_total: Money, total_weight: Weight,
                           customer: Customer) -> Money:
        if customer.customer_type in [CustomerType.PREMIUM, CustomerType.GOLD]:
            return self.premium_strategy.calculate_shipping(order_total, total_weight, customer)
        else:
            return self.standard_strategy.calculate_shipping(order_total, total_weight, customer)


# ――― Order (очищен от God Class проблем) ―――
class Order:
    """Сфокусированный класс заказа"""

    def __init__(self, customer_id: int):
        self.customer_id = customer_id
        self.items: List[OrderItem] = []
        self.status = OrderStatus.OPEN
        self.shipping_address = ""
        self.notes = ""
        self._calculator = OrderCalculator()
        self._discount_calculator = DiscountCalculator()
        self._shipping_calculator = ShippingCalculator()

    def add_item(self, product: Product, quantity: int = 1) -> None:
        order_item = OrderItem(product, quantity)
        self.items.append(order_item)

    def total_price(self) -> Money:
        return self._calculator.calculate_total_price(self.items)

    def total_weight(self) -> Weight:
        return self._calculator.calculate_total_weight(self.items)

    def calculate_discount(self, customer: Customer) -> Money:
        order_total = self.total_price()
        return self._discount_calculator.calculate_total_discount(order_total, self.items, customer)

    def calculate_shipping(self, customer: Customer) -> Money:
        order_total = self.total_price()
        total_weight = self.total_weight()
        return self._shipping_calculator.calculate_shipping(order_total, total_weight, customer)

    def get_status_display(self) -> str:
        return self.status.display_name()

    def can_be_cancelled(self) -> bool:
        return self.status.can_be_cancelled()

    def can_be_modified(self) -> bool:
        return self.status.can_be_modified()

    def get_item_count(self) -> int:
        return sum(item.quantity for item in self.items)


# ――― Payment Processing (исправлен Primitive Obsession) ―――
@dataclass(frozen=True)
class CreditCard:
    """Value object для кредитной карты"""
    number: str
    expiry: str
    cvv: str

    def __post_init__(self):
        if not self.is_valid():
            raise ValueError("Invalid credit card")

    def is_valid(self) -> bool:
        number_clean = self.number.replace(" ", "").replace("-", "")
        return (len(number_clean) == 16 and
                number_clean.isdigit() and
                len(self.cvv) in [3, 4] and
                self.cvv.isdigit())


@dataclass(frozen=True)
class PaymentRequest:
    """Parameter object вместо Long Parameter List"""
    amount: Money
    payment_method: PaymentMethod
    card: CreditCard


class PaymentProcessor:
    """Обработка платежей без Primitive Obsession"""

    def process_payment(self, request: PaymentRequest) -> bool:
        if not request.card.is_valid():
            return False

        # Расчёт комиссии
        fee_rate = request.payment_method.processing_fee_rate()
        fixed_fee = request.payment_method.fixed_fee()

        total_fee = request.amount * fee_rate + Money(fixed_fee)

        # Здесь была бы интеграция с платёжной системой
        return True


# ――― Analytics (разбили Long Method) ―――
@dataclass
class RevenueMetrics:
    """Data class для метрик выручки"""
    net_revenue: Money
    gross_revenue: Money
    tax_amount: Money
    shipping_revenue: Money
    discounts_given: Money


@dataclass
class CustomerMetrics:
    """Data class для метрик клиентов"""
    segments: Dict[CustomerType, int]
    top_customers: Dict[int, Dict[str, any]]
    avg_items_per_order: Decimal


@dataclass
class CategoryMetrics:
    """Data class для метрик категорий"""
    stats: Dict[ProductCategory, Dict[str, any]]


class RevenueAnalyzer:
    """Отвечает только за анализ выручки"""

    def analyze_revenue(self, orders: List[Order], customers: Dict[int, Customer]) -> RevenueMetrics:
        net_total = Money(Decimal('0'))
        gross_total = Money(Decimal('0'))
        tax_total = Money(Decimal('0'))
        shipping_total = Money(Decimal('0'))
        discount_total = Money(Decimal('0'))

        for order in orders:
            customer = customers.get(order.customer_id)
            if not customer:
                continue

            net_price = order.total_price()
            tax_amount = net_price * TaxRates.EUR
            gross_price = net_price + tax_amount
            shipping_cost = order.calculate_shipping(customer)
            discount_amount = order.calculate_discount(customer)

            net_total += net_price
            gross_total += gross_price
            tax_total += tax_amount
            shipping_total += shipping_cost
            discount_total += discount_amount

        return RevenueMetrics(
            net_revenue=net_total,
            gross_revenue=gross_total,
            tax_amount=tax_total,
            shipping_revenue=shipping_total,
            discounts_given=discount_total
        )


class CustomerAnalyzer:
    """Отвечает только за анализ клиентов"""

    def analyze_customers(self, orders: List[Order], customers: Dict[int, Customer]) -> CustomerMetrics:
        segments = {customer_type: 0 for customer_type in CustomerType}
        top_customers = {}
        total_items = 0

        for order in orders:
            customer = customers.get(order.customer_id)
            if not customer:
                continue

            # Сегментация
            segments[customer.customer_type] += 1

            # Топ клиенты
            if order.customer_id not in top_customers:
                top_customers[order.customer_id] = {
                    "revenue": Money(Decimal('0')),
                    "orders": 0,
                    "avg_order": Money(Decimal('0'))
                }

            order_total = order.total_price()
            top_customers[order.customer_id]["revenue"] += order_total
            top_customers[order.customer_id]["orders"] += 1

            total_items += order.get_item_count()

        # Расчёт средних значений
        for customer_stats in top_customers.values():
            if customer_stats["orders"] > 0:
                avg_amount = customer_stats["revenue"].amount / Decimal(str(customer_stats["orders"]))
                customer_stats["avg_order"] = Money(avg_amount)

        avg_items = Decimal('0')
        if orders:
            avg_items = Decimal(str(total_items)) / Decimal(str(len(orders)))

        return CustomerMetrics(
            segments=segments,
            top_customers=top_customers,
            avg_items_per_order=avg_items
        )


class CategoryAnalyzer:
    """Отвечает только за анализ категорий товаров"""

    def analyze_categories(self, orders: List[Order]) -> CategoryMetrics:
        stats = {}

        for order in orders:
            category_counts = OrderCalculator.count_items_by_category(order.items)

            for item in order.items:
                category = item.product.category
                if category not in stats:
                    stats[category] = {
                        "count": 0,
                        "revenue": Money(Decimal('0')),
                        "avg_price": Money(Decimal('0'))
                    }

                stats[category]["count"] += item.quantity
                stats[category]["revenue"] += item.total_price()

        # Расчёт средних цен
        for category_stats in stats.values():
            if category_stats["count"] > 0:
                avg_amount = category_stats["revenue"].amount / Decimal(str(category_stats["count"]))
                category_stats["avg_price"] = Money(avg_amount)

        return CategoryMetrics(stats=stats)


class DataValidator:
    """Отвечает за валидацию данных в отчётах"""

    def validate_customers(self, customers: Dict[int, Customer]) -> List[str]:
        warnings = []

        for customer in customers.values():
            if not customer.is_valid_email():
                warnings.append(f"Invalid email for customer {customer.name}")
            if customer.phone and not customer.is_valid_phone():
                warnings.append(f"Invalid phone for customer {customer.name}")

        return warnings


class ReportFormatter:
    """Отвечает только за форматирование отчётов"""

    def format_comprehensive_report(self, revenue: RevenueMetrics,
                                    customer_metrics: CustomerMetrics,
                                    category_metrics: CategoryMetrics,
                                    orders_count: int,
                                    warnings: List[str]) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("📊 COMPREHENSIVE E-COMMERCE REPORT")
        lines.append("=" * 50)
        lines.append(f"📦 Total Orders: {orders_count}")
        lines.append(f"💰 Revenue (Net): {revenue.net_revenue}")
        lines.append(f"💰 Revenue (Gross): {revenue.gross_revenue}")
        lines.append(f"🚚 Shipping Revenue: {revenue.shipping_revenue}")
        lines.append(f"🎁 Discounts Given: {revenue.discounts_given}")
        lines.append(f"📈 Avg Items/Order: {customer_metrics.avg_items_per_order:.2f}")

        # Топ клиенты
        lines.append("\n🏆 TOP CUSTOMERS (by revenue):")
        sorted_customers = sorted(
            customer_metrics.top_customers.items(),
            key=lambda x: x[1]["revenue"].amount,
            reverse=True
        )[:5]

        for i, (cid, stats) in enumerate(sorted_customers):
            lines.append(f"  {i + 1}. Customer {cid}: {stats['revenue']} ({stats['orders']} orders)")

        # Категории
        lines.append("\n📊 CATEGORY PERFORMANCE:")
        sorted_categories = sorted(
            category_metrics.stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]

        for category, stats in sorted_categories:
            lines.append(f"  {category.value}: {stats['count']} items, {stats['revenue']} revenue")

        # Сегменты клиентов
        lines.append(f"\n👥 CUSTOMER SEGMENTS:")
        for customer_type, count in customer_metrics.segments.items():
            prefix = customer_type.display_prefix().strip()
            lines.append(f"  {prefix} {customer_type.value}: {count}")

        # Предупреждения
        if warnings:
            lines.append(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings[:3]:
                lines.append(f"  - {warning}")

        lines.append("=" * 50)
        return "\n".join(lines)


class Analytics:
    """Координирует анализ, но не делает всё сам"""

    def __init__(self):
        self.revenue_analyzer = RevenueAnalyzer()
        self.customer_analyzer = CustomerAnalyzer()
        self.category_analyzer = CategoryAnalyzer()
        self.data_validator = DataValidator()
        self.report_formatter = ReportFormatter()

    def generate_comprehensive_report(self, orders: List[Order],
                                      customers: Dict[int, Customer]) -> Dict:
        # Анализ различных аспектов
        revenue_metrics = self.revenue_analyzer.analyze_revenue(orders, customers)
        customer_metrics = self.customer_analyzer.analyze_customers(orders, customers)
        category_metrics = self.category_analyzer.analyze_categories(orders)
        warnings = self.data_validator.validate_customers(customers)

        # Форматированный вывод
        formatted_report = self.report_formatter.format_comprehensive_report(
            revenue_metrics, customer_metrics, category_metrics, len(orders), warnings
        )
        print(formatted_report)

        # Возвращаем структурированные данные
        return {
            "total_orders": len(orders),
            "total_revenue_net": revenue_metrics.net_revenue.amount,
            "total_revenue_gross": revenue_metrics.gross_revenue.amount,
            "total_shipping": revenue_metrics.shipping_revenue.amount,
            "total_discounts": revenue_metrics.discounts_given.amount,
            "avg_items_per_order": customer_metrics.avg_items_per_order,
            "top_customers": customer_metrics.top_customers,
            "categories_stats": {cat.value: stats for cat, stats in category_metrics.stats.items()},
            "customer_segments": {ct.value.lower(): count for ct, count in customer_metrics.segments.items()},
            "warnings": warnings,
            "debug_log": []  # Для совместимости с тестами
        }


# ――― Тестовые данные ―――
if __name__ == "__main__":
    # Создаём продукты с правильными типами
    book = Product("Python Programming", Money(Decimal('45.99')),
                   ProductCategory.BOOKS, Weight(Decimal('0.5')))
    laptop = Product("Gaming Laptop", Money(Decimal('899.99')),
                     ProductCategory.ELECTRONICS, Weight(Decimal('2.1')))
    pen = Product("Premium Pen", Money(Decimal('12.99')),
                  ProductCategory.OFFICE, Weight(Decimal('0.1')))
    backpack = Product("Travel Backpack", Money(Decimal('79.99')),
                       ProductCategory.ACCESSORIES, Weight(Decimal('0.8')))

    # Создаём клиентов с правильными типами
    customers = {
        101: Customer(101, "Alice Johnson", "alice@email.com", CustomerType.GOLD,
                      Money(Decimal('1500.0')), 12),
        102: Customer(102, "Bob Smith", "bob@email.com", CustomerType.PREMIUM,
                      Money(Decimal('800.0')), 6),
        103: Customer(103, "Carol Davis", "carol@email.com", CustomerType.REGULAR,
                      Money(Decimal('150.0')), 2)
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