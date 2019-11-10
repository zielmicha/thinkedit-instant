import random, time

def fun1():
    return random.randrange(100)

def throw():
    xoxo

def write_to_file():
    # OK
    with open('/tmp/info.txt', 'w') as f:
        f.write('foo')

    # not OK
    with open('info.txt', 'w') as f:
        f.write('foo')

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

    try:
        write_to_file()
    except Exception as exc:
        _ = exc

    fun1()
    print(x)

    try:
        throw()
    except Exception as exc:
        pass

    _ = x
    return x

if __name__ == '__main__':
    main()
