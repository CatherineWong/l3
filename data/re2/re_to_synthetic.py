chars = "."
vowels = "V"
consonants = "C"
letters = [chr(i) for i in range(ord("a"), ord("z"))]
anchor_start  = "^"
anchor_end = "$"

def parse_regex(regex):
    regex = regex[1:-1]
    before, after = regex.split("@")
    start, match, end = [b[1:] for b in before.split(")")[:-1]]
       
    return (start, match, end), after

def match_to_language_start(match):
    language = []
    for char in match:
        if char == vowels:
            language += ["vowel"]
        elif char == consonants:
            language += ["consonant"]
        elif char == chars:
            language += ["letter"]
        else:
            language += [char]
    return " followed by a ".join(language)

def match_to_language_after(after):
    if not "\\" in after:
        language = "replace that with "
        language += " ".join([c for c in after])
    else:
        language = ""
        check = after.replace("\\2", "+")
        assert(len(check) in [1, 2])
        if "\\2\\2" in after:
            language += "double that"
        elif after.startswith("\\2"):
            after = after[2:]
            assert ("\\2" not in after)
            language += "add "
            language += " ".join([c for c in after])
            language += " after that"
        else:
            assert(after.endswith("\\2"))
            after = after[:-2]
            assert ("\\2" not in after)
            language += "add "
            language += " ".join([c for c in after])
            language += " before that"
            
    return language
        
def generate_synthetic_language(regex):
    (start, match, end), after = parse_regex(regex)
    
    language = ""
    # Before
    if len(start) > 0:
        language += f"if there is a {match_to_language_start(match)} at the start "
    elif len(end) > 0:
        language += f"if there is a {match_to_language_start(match)} at the end "
    else:
        language += f"if there is a {match_to_language_start(match)} "
    
    language += match_to_language_after(after) 
    return language
    
def main():
    DEBUG = True
    if DEBUG:
        tests = [
            "<()(s)($)@m>",
            "<(^)(.V)()@yl>",
            "<()(tV)()@g>",
            "<()(CV)()@f\\2>"
        ]
        for test in tests:
            print(test)
            print(generate_synthetic_language(test))

if __name__ == '__main__':
    main()