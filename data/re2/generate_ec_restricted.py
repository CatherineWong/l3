# Generates a restricted set of tasks with synthetic language for EC testing.
#!/usr/bin/env python2

import json
import numpy as np
import re

N_TEST = 500
MAX_SIZE = 1000

random = np.random.RandomState(0)

word_re = re.compile("^[a-z]+$")
words = []
with open("/usr/share/dict/words") as words_f:
    for line in words_f:
        word = line.strip()
        if word_re.match(word):
            words.append(word)

vowel_set = ['a', 'e', 'i', 'o', 'u']
consonant_set = ['b', 'c', 'd', 'f', 'g', 's', 'r', 't']

chars = "."
vowels = "[aeiou]"
consonants = "[^aeiou]"
# vowels = "[{}]".format("".join(vowel_set))

# Changed: consonants are no longer 'not vowels'
# consonants = "[{}]".format("".join(consonant_set))
# consonants = "[^{}]".format("".join(vowel_set))
# letters = [chr(i) for i in range(ord("a"), ord("z"))]
letters = vowel_set + consonant_set
# classes = [chars, vowels, consonants]
classes = [chars, vowels]

N_EX = 10

def sample_block(size):
    out = ""
    for i in range(size):
        use_letter = random.randint(2)
        if use_letter:
            out += random.choice(letters)
        else:
            out += random.choice(classes)
    return out

def sample_replace(size):
    out = ""
    for i in range(size):
        use_letter = random.randint(3)
        if use_letter:
            out += random.choice(letters)
        else:
            out += "\\2"
    return out

def sample():
    anchor_start = random.randint(2)
    anchor_end = not anchor_start and random.randint(2)

    start_len = random.randint(1)
    match_len = random.randint(2) + 1
    rep_len = random.randint(3)
    end_len = random.randint(1)

    start = "^" if anchor_start else ""
    start += sample_block(start_len)
    
    match = sample_block(match_len)
    if 'w' in match: print(match)
    replace = sample_replace(rep_len)

    end = sample_block(end_len)
    if anchor_end:
        end += "$"

    before = "(%s)(%s)(%s)" % (start, match, end)
    after = "\\1%s\\3" % replace

    return before, after

seen = set()
data = []
while len(data) < MAX_SIZE + N_TEST:
    before, after = sample()
    if (before, after) in seen:
        continue
    seen.add((before, after))
    matches = []
    order = list(range(len(words)))
    random.shuffle(order)
    attempts = 0
    success = True
    while len(matches) < N_EX:
        attempts += 1
        if attempts > 100:
            success = False
            break
        j = order.pop()
        word = words[j]
        sub = re.sub(before, after, word)
        if sub == word and len(matches) < N_EX / 2:
            continue
        #if sub == word:
        #    continue
        matches.append((word, sub))

    random.shuffle(matches)

    if not success:
        continue

    print(len(data))

    data.append({"before": before, "after": after, "examples": matches})


random.shuffle(data)

# Replace with restricted version and split into train / test
START = "<"
STOP = ">"
SEP = "@"

random = np.random.RandomState(0)

annotations = []

for i, example in enumerate(data):
    t_before = example["before"]
    t_before = t_before.replace(vowels, "V").replace(consonants, "C")
    re_before = t_before
    letters_before = t_before.split(")(")[1].replace(".", "").replace("V", "").replace("C", "")
    letters_before = " ".join(letters_before)
    t_before = re.sub("[a-z]+", "l", t_before)
    t_after = example["after"][2:-2]
    re_after = t_after
    letters_after = t_after.replace("\\2", "")
    letters_after = " ".join(letters_after)
    t_after = re.sub("[a-z]+", "l", t_after)
    template_key = t_before + SEP + t_after

    re_hint = START + re_before + SEP + re_after + STOP

    ex = []
    for inp, out in example["examples"]:
        inp = START + inp + STOP
        out = START + out + STOP
        ex.append((inp, out))

    annotations.append({
        "examples": ex,
        "re": re_hint,
    })

train = annotations[:MAX_SIZE]
test = annotations[MAX_SIZE:MAX_SIZE + N_TEST]

for datum in test:
    del datum["examples"][N_EX+1:]

corpus = {
    "train": train,
    "test": test
}

filename = 'corpus_{}.json'.format("".join(letters))
with open(filename, "w") as corpus_f:
    json.dump(corpus, corpus_f)

# filename = 'data_{}.json'.format("".join(letters))
# with open(filename, "w") as data_f:
#     json.dump(dataset, data_f)
