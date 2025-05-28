# Quiz по Code Smells  
Для каждого фрагмента кода выберите **основной** code smell.  
---

## Вопрос 1
```python
def process_order(customer_id, items, shipping_address, payment_method,
                  card_number, expiry_date, cvv, billing_address,
                  discount_code, gift_message, delivery_instructions):
    # Process the order...
    pass
````

- A) Long Method

Тело функции мы не видим, длину оценить нельзя

- B) **Long Parameter List** (правильно)

11 параметров! Такой метод неудобно вызывать и поддерживать. Создайте объект-параметр (`OrderRequest`, `PaymentInfo` и т. д.).

- C) Feature Envy

Проявляется, когда метод активно использует данные других классов

- D) Duplicate Code

Отсутствуют повторы кода

## Вопрос 2

```python
class Customer:
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone
    # …ещё 15 методов бизнес логики
```

- A) God Class

God Class — это класс, который занимается слишком многим (нарушает Single Responsibility Principle) и «знает» обо всём в системе. Такой класс сильно затрудняет поддержку и тестирование, поэтому рассматривается как code smell

- B) **Large Class** (правильно)

Нужно стараться делегировать часть логики другим классам, избегать раздувания класса
- C) Data Class

чаще всего Data Class считается code smell: такой класс хранит только поля без поведения, 
а бизнес-логику «распыляют» по другим местам; у нас много поведения.
- D) Duplicate Code

Отсутствуют повторы кода

## Вопрос 3

```python
def calculate_total(items):
    return sum(item.price for item in items)

def calculate_sum(products):
    return sum(prod.price for prod in products)
```

- A) Long Method

Тело функции мы не видим, длину оценить нельзя

- B) Feature Envy

Feature Envy - «зависть к функциям»: метод в одном классе чрезмерно использует данные или методы другого класса.

- C) **Duplicate Code** (правильно)

Два метода делают одно и то же; DRY (Don’t Repeat Yourself, принцип «не повторяйся!») нарушен.

- D) Magic Numbers

Magic Numbers - это «волшебные» числовые литералы, использующиеся прямо в коде (например, 0.2, 100, 5.99) без имени.

## Вопрос 4

```python
class OrderProcessor:
    def generate_report(orders):
        print("=== Sales Report ===")
        total_revenue = 0
        total_orders = len(orders)
    
        for order in orders:
            order_total = 0
            for item in order.items:
                order_total += item.price * item.quantity
            tax = order_total * 0.20
            shipping = 5.99 if order_total < 100 else 0
            final_total = order_total + tax + shipping
            total_revenue += final_total
            print(f"Order {order.id}: Items={len(order.items)}, Total=${final_total:.2f}")
    
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        print(f"Total Orders: {total_orders}")
        print(f"Total Revenue: ${total_revenue:.2f}")
        print(f"Average Order: ${avg_order:.2f}")
    
        # Generate CSV export
        csv_data = "Order ID,Items,Total\n"
        for order in orders:
            order_total = 0
            for item in order.items:
                order_total += item.price * item.quantity
            tax = order_total * 0.20
            shipping = 5.99 if order_total < 100 else 0
            final_total = order_total + tax + shipping
            csv_data += f"{order.id},{len(order.items)},{final_total:.2f}\n"
    
        with open("sales_report.csv", "w") as f:
            f.write(csv_data)
        print("Report saved to sales_report.csv")
```

- A) Magic Numbers

Да, но не только!

- B) Long Method

Да, но не только!

- C) Duplicate Code

Да, но не только!

- D) **Все вышеперечисленное** (правильно)

Long Method (Длинный метод) — свыше 30 строк, смешаны расчёты, вывод и экспорт.
Duplicate Code (Дублирование кода) — логика подсчёта заказа повторяется дважды.
Magic Numbers (Магические числа) — значения 0.20, 5.99, 100 используются без объяснения.

## Вопрос 5

```python
class ReportGenerator:
    def calculate_metrics(self, sales_data):
        total_revenue = 0
        for sale in sales_data.sales:
            total_revenue += sale.amount

        total_cost = 0
        for sale in sales_data.sales:
            total_cost += sale.cost

        average_order = total_revenue / len(sales_data.sales)

        latest_date = max(sale.date for sale in sales_data.sales)

        region_breakdown = {}
        for sale in sales_data.sales:
            region = sale.region
            region_breakdown.setdefault(region, 0)
            region_breakdown[region] += sale.amount

        return {
            "revenue": total_revenue,
            "cost": total_cost,
            "average_order": average_order,
            "latest_date": latest_date,
            "by_region": region_breakdown
        }
```

- A) **Feature Envy** (правильно)

Метод полностью «заглядывает» во внутреннюю структуру sales_data.sales (коллекция, поля amount, cost, date, region), вместо того чтобы воспользоваться готовыми методами или предоставить эту логику самому объекту SalesData.

- B) Magic numbers

Их нет.

- C) Duplicate Code

Циклы похожи, но каждый вычисляет свою метрику; дублирование не полное.

- D) Data Class

Здесь мы видим логику, а не просто класс-контейнер.


## Вопрос 6

```python
TAX_RATE = 0.08

def calculate_price(base_price, customer_type, coeff1, coeff2, coeff3, coeff4, coeff5, coeff6, coeff7, coeff8, coeff9):
    # customer_type: 1 — Regular, 2 — Premium, 3 — VIP
    if customer_type == 1:
        discount_rate = 0
    elif customer_type == 2:
        discount_rate = 0.05 * coeff1 / coeff7
    elif customer_type == 3:
        discount_rate = (0.12 + coeff2) * coeff3
    else:
        discount_rate = 0
    
    discounted_price = coeff4 * base_price * (1 - discount_rate)
    tax = discounted_price * TAX_RATE * coeff5 / coeff6
    final_price = coeff9 * discounted_price + tax + coeff8

    return final_price
```

- A) Long Parameter List

Да, но не только!

- C) Both Magic Numbers

Да, но не только!

- B) Switch Statements

Да, но не только!

- D) **Все вышеперечисленное** (правильно)

Используются «сырые» целочисленные коды для типов клиентов вместо enum или специальных объектов.
Присутствуют магические числа (0.05, 0.12)
Присутствует развесистая условная логика (if/elif)
