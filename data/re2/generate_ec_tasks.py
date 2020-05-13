"""
Generates tasks and language files for Dreamcoder.
"""
import argparse
import json
import os
import random

from re_to_synthetic import generate_synthetic_language

random.seed(0)

parser = argparse.ArgumentParser()
parser.add_argument("--taskDatasetDir",
                        default="data/re2/tasks")
parser.add_argument("--languageDatasetDir",
                default="data/re2/language")

parser.add_argument("--startingCorpus",
                type=str,
                default="corpus",
                help="Corpus of data to start.")
                    
parser.add_argument("--generateTaskDataset",
                choices=[
                    "re2_3000",
                    "re2_1000",
                    "re2_500",
                    "re2_10"],
                default=None,
                help="Generates pre-cached dataset and stores it under the top-level path.")
parser.add_argument("--generateLanguageDataset",
                choices=[
                    "human",
                    "synthetic"],
                default=None,
                help="Generates language dataset and stores it under the top-level path.")
parser.add_argument("--no_vowels_consonants",
                    action="store_true")
args = parser.parse_args()
def main():
    task_dataset = args.generateTaskDataset
    language_dataset = args.generateLanguageDataset
    def get_n_tasks(task_dataset):
        if len(task_dataset.split("_")) < 2:
            return None
        else:
            return int(task_dataset.split("_")[-1])
    n_tasks = get_n_tasks(task_dataset)
    
    starting_corpus = args.startingCorpus
    def get_restricted_letters(starting_corpus):
        if len(starting_corpus.split("_")) < 2:
            return None
        else:
            return starting_corpus.split("_")[-1]
    restricted_letters = get_restricted_letters(starting_corpus)
    if restricted_letters is not None:
        task_dataset += "_{}".format(restricted_letters)
    
    no_vowels_consonants = args.no_vowels_consonants
    if no_vowels_consonants:
        task_dataset += "_novc"

    task_dataset_path = os.path.join(args.taskDatasetDir, task_dataset)
    language_dataset_path = os.path.join(args.languageDatasetDir, task_dataset, language_dataset)
    
    corpus_f = "{}.json".format(args.startingCorpus)
    with open(corpus_f, 'rb') as f:
        corpus = json.load(f)
    
    for split in ("train", "test"):
        from pathlib import Path
        split_path = os.path.join(task_dataset_path, split)
        Path(split_path).mkdir(parents=True, exist_ok=True)
        raw_split = corpus[split]
        if split == "train":
            n_tasks = len(raw_split) if n_tasks is None else n_tasks
        else:
            n_tasks = len(raw_split)
        
        
        def convert_examples(examples):
            # Convert to input/output list of characters.
            def convert_example(x):
                x = x[1:-1] # Remove < > tokens
                return [c for c in x]
            valid = True
            converted = []
            for x, y in examples:
                new_x, new_y = convert_example(x), convert_example(y)
                if not ((len(new_x) > 1) and (len(new_y) > 1)): 
                    valid = False
                converted += [ ( (convert_example(x),),
                      convert_example(y))]
            return converted, valid

        # Name the tasks.
        original_tasks = []
        for (i, t) in enumerate(raw_split[:n_tasks]):
            examples, valid = convert_examples(t["examples"])
            if valid:
                original_tasks.append({
                    "name": f"re2_{split}_{i}",
                    "examples": examples
                })
            else:
                print("Found invalid!")
        print(f"Found n=[{len(original_tasks)}] original tasks.")
        synthetic_language = {}
        for i, t in enumerate(raw_split[:n_tasks]):
            original_name = f"re2_{split}_{i}" 
            synthetic = generate_synthetic_language(t["re"])
            has_vowel_consonant = ('vowel' in synthetic) or ('consonant' in synthetic)
            synthetic_language[original_name] = {
                "language" : [synthetic],
                "has_vowel" : has_vowel_consonant
            }
        
        # Rename the tasks and remove any sequences
        final_tasks = []
        renamed = {}
        for t in original_tasks:
            has_vowel = synthetic_language[t["name"]]["has_vowel"]
            if no_vowels_consonants and has_vowel: continue
            final_tasks.append(t)
            new_name = t["name"] + "_" + "_".join(synthetic_language[t["name"]]["language"][0].split())
            renamed[t["name"]] = new_name
            t["name"] = new_name

        print(f"Writing n=[{len(final_tasks)}]/[{len(original_tasks)}] tasks to {split_path}/tasks.json")
        with open(os.path.join(split_path, "tasks.json"), "w") as f:
            json.dump(final_tasks, f)
        
        if language_dataset == "human":
            split_path = os.path.join(language_dataset_path, split)
            Path(split_path).mkdir(parents=True, exist_ok=True)
            
            language = {
                renamed[f"re2_{split}_{i}"] : [" ".join(sentence) for sentence in t['hints_aug']]
                for i, t in enumerate(raw_split[:n_tasks]) if f"re2_{split}_{i}" in renamed
            }
            print(f"Writing language for n=[{len(language)}]/[{len(raw_split)}] tasks to {split_path}/language.json")
            with open(os.path.join(split_path, "language.json"), 'w') as f:
                json.dump(language, f)
                
            # Write vocabulary.
            vocabulary = set()
            for t in raw_split[:n_tasks]:
                for sentence in t["hints_aug"]:
                    vocabulary.update(sentence)
            print(f"Writing a vocabulary of n={len(vocabulary)} to {split_path}/vocab.json")
            with open(os.path.join(split_path,"vocab.json"), 'w') as f:
                json.dump(list(vocabulary), f)
        
        if language_dataset == "synthetic":
            split_path = os.path.join(language_dataset_path, split)
            Path(split_path).mkdir(parents=True, exist_ok=True)
            language = {
                renamed[f"re2_{split}_{i}"] : [generate_synthetic_language(t["re"])]
                for i, t in enumerate(raw_split[:n_tasks]) if f"re2_{split}_{i}" in renamed
            }
            
            print(f"Writing language for n=[{len(language)}]/[{len(raw_split)}] tasks to {split_path}/language.json")
            with open(os.path.join(split_path, "language.json"), 'w') as f:
                json.dump(language, f)
                
            # Write vocabulary.
            vocabulary = set()
            for sentences in language.values():
                for sentence in sentences:
                    vocabulary.update(sentence.split(" "))
            print(f"Writing a vocabulary of n={len(vocabulary)} to {split_path}/vocab.json")
            with open(os.path.join(split_path,"vocab.json"), 'w') as f:
                json.dump(list(vocabulary), f)
            
    
        


if __name__ == '__main__':
    main()