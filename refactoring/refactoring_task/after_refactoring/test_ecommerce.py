"""
test_ecommerce.py
Unit tests для проверки функциональности до рефакторинга.
Эти тесты должны проходить до и после рефакторинга, обеспечивая
что мы не сломали существующую логику.
"""

import unittest
from io import StringIO
from unittest.mock import patch

# Импортируем наш код из файла ecommerce.py в той же папке
try:
    from refactoring.refactoring_task.before_refactoring.ecommerce import (
        Product, Order, Customer, DiscountHelper, ShippingCalculator,
        Analytics, OrderProcessor,
        TAX_RATE, LOYALTY_DISCOUNT, FREE_SHIPPING_THRESHOLD,
        PREMIUM_CUSTOMER_TYPE, GOLD_CUSTOMER_TYPE, REGULAR_CUSTOMER_TYPE
    )
except ImportError as e:
    print("❌ Ошибка импорта! Убедитесь что файл ecommerce.py находится в той же папке.")
    print(f"Детали ошибки: {e}")
    exit(1)


class TestProductAndOrder(unittest.TestCase):
    """Тестируем базовую функциональность Product и Order"""

    def setUp(self):
        """Подготавливаем тестовые данные"""
        self.product1 = Product("Book", 25.0, "books", 0.3)
        self.product2 = Product("Pen", 5.0, "office", 0.1)
        self.order = Order(customer_id=123)

    def test_product_creation(self):
        """Тест создания продукта"""
        self.assertEqual(self.product1.name, "Book")
        self.assertEqual(self.product1.price, 25.0)
        self.assertEqual(self.product1.category, "books")
        self.assertEqual(self.product1.weight, 0.3)

    def test_order_add_items(self):
        """Тест добавления товаров в заказ"""
        self.order.add_item(self.product1, 2)
        self.order.add_item(self.product2, 1)

        # Проверяем что товары добавились (с учётом примитивной реализации quantity)
        self.assertEqual(len(self.order.items), 3)  # 2 книги + 1 ручка
        self.assertEqual(self.order.customer_id, 123)
        self.assertEqual(self.order.status, "OPEN")

    def test_order_total_price_methods(self):
        """Тест методов подсчёта общей стоимости (включая дублированный код)"""
        self.order.add_item(self.product1, 2)  # 2 * 25 = 50
        self.order.add_item(self.product2, 1)  # 1 * 5 = 5
        # Итого: 55

        # Оба метода должны возвращать одинаковый результат (несмотря на duplicate code)
        total1 = self.order.total_price()
        total2 = self.order.grand_total()

        self.assertEqual(total1, 55.0)
        self.assertEqual(total2, 55.0)
        self.assertEqual(total1, total2)  # Проверяем что duplicate code работает одинаково

    def test_order_shipping_calculation(self):
        """Тест расчёта доставки"""
        # Заказ меньше FREE_SHIPPING_THRESHOLD
        self.order.add_item(self.product2, 1)  # 5.0, weight 0.1
        shipping = self.order.calculate_shipping()
        self.assertEqual(shipping, 5.99)  # light weight, low price

        # Заказ больше FREE_SHIPPING_THRESHOLD
        expensive_product = Product("Laptop", 150.0, "electronics", 2.0)
        order2 = Order(456)
        order2.add_item(expensive_product, 1)
        shipping2 = order2.calculate_shipping()
        self.assertEqual(shipping2, 0)  # free shipping over 100

    def test_order_status_display(self):
        """Тест отображения статуса заказа"""
        self.assertEqual(self.order.get_status_display(), "📝 Open")

        self.order.status = "SHIPPED"
        self.assertEqual(self.order.get_status_display(), "🚚 Shipped")

        self.order.status = "UNKNOWN_STATUS"
        self.assertEqual(self.order.get_status_display(), "❓ Unknown")

    def test_order_status_permissions(self):
        """Тест проверки разрешений для статуса заказа"""
        # OPEN заказ можно отменить и изменить
        self.order.status = "OPEN"
        self.assertTrue(self.order.can_be_cancelled())
        self.assertTrue(self.order.can_be_modified())

        # SHIPPED заказ нельзя отменить и изменить
        self.order.status = "SHIPPED"
        self.assertFalse(self.order.can_be_cancelled())
        self.assertFalse(self.order.can_be_modified())


class TestCustomerFunctionality(unittest.TestCase):
    """Тестируем Large Class Customer и его множественные ответственности"""

    def setUp(self):
        self.regular_customer = Customer(1, "John Doe", "john@email.com",
                                         REGULAR_CUSTOMER_TYPE, 100.0, 5)
        self.premium_customer = Customer(2, "Jane Smith", "jane@email.com",
                                         PREMIUM_CUSTOMER_TYPE, 500.0, 10)
        self.gold_customer = Customer(3, "Bob Gold", "bob@email.com",
                                      GOLD_CUSTOMER_TYPE, 2000.0, 25)

    def test_customer_email_validation(self):
        """Тест валидации email (часть Large Class проблемы)"""
        self.assertTrue(self.regular_customer.is_valid_email())

        invalid_customer = Customer(99, "Invalid", "invalid-email",
                                    REGULAR_CUSTOMER_TYPE, 0, 0)
        self.assertFalse(invalid_customer.is_valid_email())

    def test_customer_phone_validation(self):
        """Тест валидации телефона"""
        self.regular_customer.phone = "123-456-7890"
        self.assertTrue(self.regular_customer.is_valid_phone())

        self.regular_customer.phone = "123"
        self.assertFalse(self.regular_customer.is_valid_phone())

    def test_customer_display_names(self):
        """Тест форматирования имён (ещё одна ответственность Large Class)"""
        self.assertEqual(self.regular_customer.get_display_name(), "John Doe")
        self.assertEqual(self.premium_customer.get_display_name(), "⭐ Jane Smith")
        self.assertEqual(self.gold_customer.get_display_name(), "🥇 Bob Gold")

    def test_customer_loyalty_multipliers(self):
        """Тест бизнес-логики лояльности (тоже в Large Class)"""
        self.assertEqual(self.regular_customer.get_loyalty_multiplier(), 0.05)
        self.assertEqual(self.premium_customer.get_loyalty_multiplier(), 0.10)
        self.assertEqual(self.gold_customer.get_loyalty_multiplier(), 0.15)

    def test_customer_free_shipping_eligibility(self):
        """Тест права на бесплатную доставку"""
        self.assertFalse(self.regular_customer.can_get_free_shipping())
        self.assertTrue(self.premium_customer.can_get_free_shipping())
        self.assertTrue(self.gold_customer.can_get_free_shipping())

    def test_customer_update_spent_amount(self):
        """Тест обновления потраченной суммы"""
        initial_spent = self.regular_customer.total_spent
        initial_orders = self.regular_customer.orders_count

        self.regular_customer.update_spent_amount(50.0)

        self.assertEqual(self.regular_customer.total_spent, initial_spent + 50.0)
        self.assertEqual(self.regular_customer.orders_count, initial_orders + 1)


class TestDiscountsAndShipping(unittest.TestCase):
    """Тестируем Feature Envy классы DiscountHelper и ShippingCalculator"""

    def setUp(self):
        self.discount_helper = DiscountHelper()
        self.shipping_calc = ShippingCalculator()

        # Создаём тестовые данные
        self.product = Product("Test Product", 30.0, "test", 1.0)
        self.order = Order(customer_id=1)
        self.order.add_item(self.product, 3)  # 3 items, total 90.0

        self.regular_customer = Customer(1, "John", "john@email.com",
                                         REGULAR_CUSTOMER_TYPE, 100.0, 5)
        self.premium_customer = Customer(2, "Jane", "jane@email.com",
                                         PREMIUM_CUSTOMER_TYPE, 500.0, 10)

    def test_loyalty_discount_calculation(self):
        """Тест расчёта скидки лояльности (Feature Envy)"""
        # Regular customer needs 3+ items for discount
        discount = self.discount_helper.calc_loyalty_discount(self.order, self.regular_customer)
        expected = 90.0 * 0.05  # base_price * regular_multiplier
        self.assertEqual(discount, expected)

        # Premium customer needs 2+ items
        discount_premium = self.discount_helper.calc_loyalty_discount(self.order, self.premium_customer)
        expected_premium = 90.0 * 0.10
        self.assertEqual(discount_premium, expected_premium)

    def test_bulk_discount_calculation(self):
        """Тест скидки за оптовую покупку"""
        # Создаём заказ с 5+ товарами одной категории
        bulk_order = Order(customer_id=1)
        for _ in range(6):  # 6 товаров одной категории
            bulk_order.add_item(self.product, 1)

        discount = self.discount_helper.calc_bulk_discount(bulk_order)
        expected = 6 * 2.5  # count * magic_number
        self.assertEqual(discount, expected)

    def test_advanced_shipping_calculation(self):
        """Тест продвинутого расчёта доставки (Feature Envy)"""
        # Regular customer
        shipping = self.shipping_calc.calculate_advanced_shipping(self.order, self.regular_customer)
        expected = 3.0 * 2.5 + 3.99  # total_weight * rate + base
        self.assertEqual(shipping, expected)

        # Premium customer with free shipping eligibility
        expensive_order = Order(customer_id=2)
        expensive_product = Product("Expensive", 60.0, "luxury", 1.0)
        expensive_order.add_item(expensive_product, 1)

        shipping_premium = self.shipping_calc.calculate_advanced_shipping(expensive_order, self.premium_customer)
        self.assertEqual(shipping_premium, 0)  # Free shipping


class TestAnalyticsReporting(unittest.TestCase):
    """Тестируем Long Method в Analytics классе"""

    def setUp(self):
        self.analytics = Analytics()

        # Создаём тестовые данные
        self.products = [
            Product("Book", 25.0, "books", 0.5),
            Product("Pen", 5.0, "office", 0.1),
            Product("Laptop", 500.0, "electronics", 2.0)
        ]

        self.customers = {
            101: Customer(101, "Alice", "alice@email.com", GOLD_CUSTOMER_TYPE, 1000.0, 10),
            102: Customer(102, "Bob", "bob@email.com", REGULAR_CUSTOMER_TYPE, 200.0, 3)
        }

        # Создаём заказы
        self.orders = []

        order1 = Order(101)
        order1.add_item(self.products[0], 2)  # 2 books = 50
        order1.add_item(self.products[1], 1)  # 1 pen = 5
        order1.status = "DELIVERED"
        self.orders.append(order1)

        order2 = Order(102)
        order2.add_item(self.products[2], 1)  # 1 laptop = 500
        order2.status = "SHIPPED"
        self.orders.append(order2)

    @patch('sys.stdout', new_callable=StringIO)
    def test_comprehensive_report_generation(self, mock_stdout):
        """Тест генерации comprehensive report (Long Method)"""
        report = self.analytics.generate_comprehensive_report(self.orders, self.customers)

        # Проверяем основные метрики
        self.assertEqual(report["total_orders"], 2)
        self.assertEqual(report["total_revenue_net"], 555.0)  # 55 + 500

        # Проверяем что gross revenue включает налоги
        expected_gross = 555.0 * 1.2  # с налогом 20%
        self.assertAlmostEqual(report["total_revenue_gross"], expected_gross, places=2)

        # Проверяем avg items per order
        expected_avg = (3 + 1) / 2  # (order1: 3 items, order2: 1 item) / 2 orders
        self.assertEqual(report["avg_items_per_order"], expected_avg)

        # Проверяем что есть данные по клиентам
        self.assertIn(101, report["top_customers"])
        self.assertIn(102, report["top_customers"])

        # Проверяем категории
        self.assertIn("books", report["categories_stats"])
        self.assertIn("office", report["categories_stats"])
        self.assertIn("electronics", report["categories_stats"])

        # Проверяем сегменты клиентов
        self.assertEqual(report["customer_segments"]["gold"], 1)
        self.assertEqual(report["customer_segments"]["regular"], 1)

        # Проверяем что было логирование
        self.assertGreater(len(report["debug_log"]), 0)

        # Проверяем что отчёт был выведен на экран
        output = mock_stdout.getvalue()
        self.assertIn("COMPREHENSIVE E-COMMERCE REPORT", output)
        self.assertIn("Total Orders: 2", output)


class TestPrimitiveObsessionAndOtherSmells(unittest.TestCase):
    """Тестируем Primitive Obsession и другие code smells"""

    def test_order_processor_payment_methods(self):
        """Тест Switch Statement в OrderProcessor (Primitive Obsession)"""
        processor = OrderProcessor()

        # Тестируем разные валюты
        self.assertTrue(processor.process_payment(100.0, "EUR", "CREDIT",
                                                  "1234567890123456", "12/25", "123"))
        self.assertTrue(processor.process_payment(100.0, "USD", "DEBIT",
                                                  "1234567890123456", "12/25", "123"))
        self.assertFalse(processor.process_payment(100.0, "INVALID", "CREDIT",
                                                   "1234567890123456", "12/25", "123"))

        # Тестируем разные способы оплаты
        self.assertTrue(processor.process_payment(100.0, "EUR", "PAYPAL",
                                                  "1234567890123456", "12/25", "123"))
        self.assertFalse(processor.process_payment(100.0, "EUR", "BITCOIN",
                                                   "1234567890123456", "12/25", "123"))

        # Тестируем валидацию карты (примитивная проверка строк)
        self.assertFalse(processor.process_payment(100.0, "EUR", "CREDIT",
                                                   "123", "12/25", "123"))  # короткий номер
        self.assertFalse(processor.process_payment(100.0, "EUR", "CREDIT",
                                                   "1234567890123456", "12/25", "12"))  # короткий CVV


if __name__ == "__main__":
    # Запускаем все тесты
    unittest.main(verbosity=2)