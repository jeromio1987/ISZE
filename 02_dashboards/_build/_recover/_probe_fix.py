b = open(r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\build_db_leakage_review.py', encoding='utf-8').read()
frag = chr(43) + chr(92) + chr(39) + ' distributors' + chr(92) + chr(39) + chr(41)
print('target fragment:', repr(frag))
print('occurrences in file:', b.count(frag))
for i in range(len(b)):
    pass
start = 0
while True:
    i = b.find(frag, start)
    if i == -1:
        break
    print('at char', i)
    print('   LHS:', repr(b[i - 50:i]))
    print('   RHS:', repr(b[i + len(frag):i + len(frag) + 10]))
    start = i + 1
print()
# what does the rest of the script use for the "otherwise nothing" idiom?
for pat in [chr(58) + chr(39) + chr(39), chr(63) + chr(39) + ' ', 'cn<22']:
    print(repr(pat), 'count', b.count(pat))
print()
# show the two neighbouring lines that already use :'' style commas/colons
for pat in ["cn<22?", "dbs.length"]:
    print(f'--- {pat!r} ---')
    st = 0
    while True:
        i = b.find(pat, st)
        if i == -1:
            break
        print('   at', i, repr(b[i - 30:i + 60]))
        st = i + 1
