import random

def fun1():
    return random.randrange(100)

def main():
    x = 5
    y = 6
    x += 1
    x, y = y, x

    a = {}

    for z in [1,4]:
        for a in [1, 2]:
            x += z

        x += 100

    fun1()
    print(x)

    1/0

    _ = x
    return x

if __name__ == '__main__':
    main()
