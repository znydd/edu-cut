def decor(fn):
    print(fn())


@decor
def show_msg():
    return "good morning"
