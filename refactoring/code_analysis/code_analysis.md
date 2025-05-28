# Задания для проверки понимания материала

## Аналитическое задание

### Задание 1: Анализ кода
```python
def calculate_total(items):
    total = 0
    for item in items:
        if item['type'] == 'book':
            total += item['price'] * 0.9  # 10% скидка на книги
        elif item['type'] == 'food':
            total += item['price'] * 0.95  # 5% скидка на еду
        else:
            total += item['price']
    return total
```

**Вопросы для анализа:**
1. Какие проблемы с точки зрения принципов SOLID вы видите в этом коде?
2. Как бы вы улучшили этот код, применяя принцип Open/Closed?
3. Какие паттерны проектирования могли бы помочь сделать этот код более гибким?

### Решение задания 1:

1. **Проблемы с точки зрения SOLID:**
   - Нарушение принципа Single Responsibility: функция выполняет и расчет суммы, и определение скидок
   - Нарушение принципа Open/Closed: для добавления нового типа товара нужно изменять существующий код
   - Нарушение принципа Interface Segregation: код жестко привязан к конкретной структуре данных
   - Нарушение принципа Dependency Inversion: высокоуровневая логика зависит от деталей реализации

2. **Улучшение с применением Open/Closed:**
```python
from abc import ABC, abstractmethod

class DiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, price: float) -> float:
        pass

class BookDiscount(DiscountStrategy):
    def calculate_discount(self, price: float) -> float:
        return price * 0.9

class FoodDiscount(DiscountStrategy):
    def calculate_discount(self, price: float) -> float:
        return price * 0.95

class NoDiscount(DiscountStrategy):
    def calculate_discount(self, price: float) -> float:
        return price

def calculate_total(items, discount_strategies):
    total = 0
    for item in items:
        strategy = discount_strategies.get(item['type'], NoDiscount())
        total += strategy.calculate_discount(item['price'])
    return total
```

3. **Подходящие паттерны проектирования:**
   - Strategy: для инкапсуляции различных стратегий расчета скидок
   - Factory: для создания объектов стратегий
   - Decorator: для комбинирования различных скидок

## Практическое задание

### Задание 2: Рефакторинг
Дан следующий код:

```python
class Order:
    def __init__(self):
        self.items = []
        self.total = 0
    
    def add_item(self, item):
        self.items.append(item)
        if item['type'] == 'book':
            self.total += item['price'] * 0.9
        elif item['type'] == 'food':
            self.total += item['price'] * 0.95
        else:
            self.total += item['price']
    
    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            if item['type'] == 'book':
                self.total -= item['price'] * 0.9
            elif item['type'] == 'food':
                self.total -= item['price'] * 0.95
            else:
                self.total -= item['price']
```

### Решение задания 2:

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class DiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, price: float) -> float:
        pass

class BookDiscount(DiscountStrategy):
    def calculate_discount(self, price: float) -> float:
        return price * 0.9

class FoodDiscount(DiscountStrategy):
    def calculate_discount(self, price: float) -> float:
        return price * 0.95

class NoDiscount(DiscountStrategy):
    def calculate_discount(self, price: float) -> float:
        return price

class DiscountCalculator:
    def __init__(self):
        self._strategies: Dict[str, DiscountStrategy] = {
            'book': BookDiscount(),
            'food': FoodDiscount()
        }
    
    def get_strategy(self, item_type: str) -> DiscountStrategy:
        return self._strategies.get(item_type, NoDiscount())
    
    def calculate_price(self, item: dict) -> float:
        strategy = self.get_strategy(item['type'])
        return strategy.calculate_discount(item['price'])

class Order:
    def __init__(self):
        self.items: List[dict] = []
        self.total: float = 0
        self._discount_calculator = DiscountCalculator()
    
    def add_item(self, item: dict) -> None:
        self.items.append(item)
        self.total += self._discount_calculator.calculate_price(item)
    
    def remove_item(self, item: dict) -> None:
        if item in self.items:
            self.items.remove(item)
            self.total -= self._discount_calculator.calculate_price(item)
    
    def add_discount_strategy(self, item_type: str, strategy: DiscountStrategy) -> None:
        self._discount_calculator._strategies[item_type] = strategy
```

**Объяснение решения:**

1. **Применение Single Responsibility Principle:**
   - Класс `DiscountCalculator` отвечает только за расчет скидок
   - Класс `Order` отвечает только за управление заказом
   - Каждый класс стратегии скидок отвечает за свой тип скидки

2. **Применение паттерна Strategy:**
   - Создан абстрактный класс `DiscountStrategy`
   - Конкретные реализации для разных типов скидок
   - Легко добавлять новые типы скидок

3. **Улучшения:**
   - Добавлена типизация для лучшей читаемости
   - Добавлен метод `add_discount_strategy` для динамического добавления новых типов скидок
   - Улучшена инкапсуляция через использование приватных методов и атрибутов
   - Код стал более тестируемым благодаря разделению ответственности

4. **Преимущества нового решения:**
   - Легко добавлять новые типы скидок без изменения существующего кода
   - Улучшена читаемость и поддерживаемость кода
   - Уменьшено дублирование кода
   - Соблюдены все принципы SOLID 