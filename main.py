# 1 этап. Порождение грамматик
from functools import reduce
# Считать имя файла источника. Если пустое - text.txt
try:
    source = input('Файл-источник: ')
except EOFError:
    source = 'text.txt'
if len(source) == 0:
    source = 'text.txt'

# Считать источник по строкам
with open(source, 'r', encoding='utf-8') as fi:
    text = fi.read().replace('\n', ' ').lower().split()
print('Исходый текст:', *text)

# Составить словарь. Строки разбить на слова, убрать все знаки препинания,
# присоединить к словарю, отсортировать по длине
vocab = sorted(set([w.strip('.,:;<>?/\'"|\\~•`!@#$%^&*()_-+=[]{}№') for w in text]), key=len, reverse=True)
print('Словарь:', *vocab)

# Составить алфавит, отсортировать
abc = sorted(set(reduce(lambda letters, x: letters.union([c for c in x if c.isalnum()]), vocab, set())))
print('Алфавит:', *abc)
with open('text.voc', 'w', encoding='utf-8') as fv, open('text.abc', 'w', encoding='utf-8') as fa:
    [print(w, file=fv) for w in vocab]
    print(*abc, file=fa)


# Функция ищет правило с левой частью = an, в правой части терминальный начальный символ слова w,
# возвращает нетерминальную часть или -1 если не найдено
def rulex(w, an):
    for r in rules:
        if len(w) > 0 and w[0] == r.right[0] and an == r.left:
            return r.right[1]
    return -1


# Функция строит все цепочки из узла rr длиной <= n
def getchaines(rp, n):
    if n == 0 or rp.right[1] == 0:
        return {rp.right[0]}
    result = set()
    for r in rules:
        if rp.right[1] == r.left:
            result |= set([rp.right[0] + r for r in getchaines(r, n - 1)])
    return result


def twinremove():
    # Удаляем дубли
    cnt = len(rules) - 1
    while cnt > 1:
        for i in range(cnt - 1, 0, -1):
            if rules[cnt].left == rules[i].left and rules[cnt].right == rules[i].right:
                del rules[cnt]
                cnt -= 1
        cnt -= 1


# Правило вывода: left - левая часть (0 - начало), rstr - терминальная правая часть,
# rnterm - нетерминальная правая часть (0 - окончание)
class Rule:
    def __init__(self, left=0, rstr='', rnterm=0):
        self.left = left
        self.right = (rstr, rnterm)


maxlen = len(vocab[0])  # Максимальная длина слова
rules, cnt, cntl = [], 1, 0  # Список правил, следующий номер для нового правила, локальный номер для поиска

# По словам словаря
for w in vocab:
    cntl = 0
# Ищем по цепочке от начала (0) до первого несовпадения
    while rulex(w, cntl) >= 0:
        cntl = rulex(w, cntl)
        w = w[1:]
# Далее строить новую подцепочку. Если слово максимальной длины, остаточное правило длины 2, иначе 1
    if len(w) == maxlen:
        restlen = 2
    else:
        restlen = 1

# Строим новую ветвь дерева от последнего совпавшего узла
    while len(w) > restlen:
        rules.append(Rule(cntl, w[0], cnt))
        w, cntl, cnt = w[1:], cnt, cnt + 1
    rules.append(Rule(cntl, w))

# Проверить, что остаток цепочки максимальной длины является суффиксом цепочки меньшей длины
    if maxlen == 2 and all(not r.endswith(w) for r in vocab if len(r) < maxlen):
        vocab.append(w)

# Распечатать и сохранить в файле правила отсортированные по левой части
rules = sorted(rules, key=lambda x: x.left)
[print(r.left, '->', *r.right) for r in sorted(rules, key=lambda x: x.left)]
print()
with open('text.rul', 'w', encoding='utf-8') as fr:
    [print(r.left, '->', *r.right, file=fr) for r in rules]

# 2 этап Получение рекурсивной грамматики
# Соединение правил остатка длины 2 с неостаточными цепочками
# Выбираем все остаточные правила длины 2
restrules = [[r, None, None] for r in rules if len(r.right[0]) == 2]

for r in restrules:
    rr, rn, rm = r[0].left, r[0].right[0][0], r[0].right[0][1]
    # Ищем правило n для правила r по второму символу
    for i in range(len(rules)):
        if rules[i].right[1] == 0 and len(rules[i].right[0]) == 1 and rules[i].right[0] == rm:
            # Ищем правило m для правила n по левой части и для правила r по первому символу
            for j in range(i - 1, 0, -1):
                if rules[j].right[1] == rules[i].left and rules[j].right[0] == rn:
                    # Если найдены n, m - заносим в список к правилу r
                    r[1], r[2] = rules[j], rules[i]
                    break
        if r[2] is not None:
            break
# По списку производим замену
for r in restrules:
    if r[1] is not None:
        rules.remove(r[0])
        for rule in rules:
            if rule.right[1] == r[0].left:  # Если правая часть совпадает с r - заменить на n
                rule.right = (rule.right[0], r[1].left)
            if rule.left == r[0].left:  # Если левая часть совпадает с r - заменить на n
                rule.left = r[1].left
# Удалить дубли
twinremove()
print('***2 part end')
[print(r.left, '->', *r.right) for r in rules]

# 3 этап Объединение совпадающих цепочек
chaineslist = []
i = 0
while i < len(rules):
    # Получить все цепочки для узла rch длиной не более len(rules)
    chaines = getchaines(rules[i], len(rules))
    chuniq = True
    for ch in chaineslist:
        # Если множество цепочек проверяемого Aj эквивалентно сохранённому уникальному множеству цепочек узла Ai
        if chaines == ch[1]:
            aj, ai = ch[0].left, rules[i].left
            # Поменять все вхождения Aj на Ai и в левых и в правых частях правил вывода в основном списке
            for rr in rules:
                if rr.left == aj:
                    rr.left = ai
                if rr.right[1] == aj:
                    rr.right = (rr.right[0], ai)
            # и в списке для проверки множества цепочек
            for rch in chaineslist:
                if rch[0].left == aj:
                    rch[0].left = ai
                if rch[0].right[1] == aj:
                    rch[0].right = (rch[0].right[0], ai)
            chuniq = False
            break
    # Если не нашлось узла Ai, на который поменяли Aj, множество цепочек уникально, сохраняем его с узлом
    if chuniq:
        chaineslist.append((rules[i], chaines))
    i += 1
# Удалить дубли
twinremove()
print('*** 3 part end: new rules:')
[print(r.left, '->', *r.right) for r in rules]
# Сохраняем результат в файле text.res
with open('text.res', 'w',  encoding='utf-8') as fr:
    [print(r.left, '->', *r.right, file=fr) for r in rules]
