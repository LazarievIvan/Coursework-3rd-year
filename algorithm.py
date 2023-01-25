def find_sum_of_all_whole_divisors(n):
    i = 1
    div_sum = 0
    while i < n:
        remainder = n % i
        if remainder == 0:
            div_sum = div_sum + i
        i = i + 1
    return div_sum


a = 11
b = 10
a = a if a < b else b
print(a)
divisors_sum = find_sum_of_all_whole_divisors(a)
print(divisors_sum)
