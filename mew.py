results = []
def summ(a, b):
    return a + b
def subtract(a, b):
    return a - b
def manager(choice, a, b):
    if choice == 1:
        results.append(summ(a, b))
    elif choice == 2:
        results.append(subtract(a, b))
    else:
        print("Неверный выбор")

while True:
    choice = int(input("Выберите операцию (1 - сложение, 2 - вычитание, 0 - выход): "))
    if choice == 0:
        break
    if choice not in (1, 2):
        continue

    a = int(input("Введите первое число: "))
    b = int(input("Введите второе число: "))
    manager(choice, a, b)

print("Результат:", results)