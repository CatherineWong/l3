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
parser.add_argument("--generateTaskDataset",
                choices=[
                    "re2_3000",
                    "re2_1000",
                    "re2_500"],
                default=None,
                help="Generates pre-cached dataset and stores it under the top-level path.")
parser.add_argument("--generateLanguageDataset",
                choices=[
                    "human",
                    "synthetic"],
                default=None,
                help="Generates language dataset and stores it under the top-level path.")
args = parser.parse_args()
def main():
    task_dataset = args.generateTaskDataset
    language_dataset = args.generateLanguageDataset
    task_dataset_path = os.path.join(args.taskDatasetDir, task_dataset)
    language_dataset_path = os.path.join(args.languageDatasetDir, task_dataset, language_dataset)
    
    def get_n_tasks(task_dataset):
        if len(task_dataset.split("_")) < 2:
            return None
        else:
            return int(task_dataset.split("_")[-1])
    n_tasks = get_n_tasks(task_dataset)
    
    with open('corpus.json', 'rb') as f:
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
        
        tasks = [   {
                    "name": f"re2_{split}_{i}",
                    "examples": t["examples"]
                    } 
                for (i, t) in enumerate(raw_split[:n_tasks])]

        print(f"Writing n=[{len(tasks)}]/[{len(raw_split)}] tasks to {split_path}/tasks.json")
        with open(os.path.join(split_path, "tasks.json"), "w") as f:
            json.dump(tasks, f)
        
        if language_dataset == "human":
            split_path = os.path.join(language_dataset_path, split)
            Path(split_path).mkdir(parents=True, exist_ok=True)
            
            language = {
                f"re2_{split}_{i}" : [" ".join(sentence) for sentence in t['hints_aug']]
                for i, t in enumerate(raw_split[:n_tasks])
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
                f"re2_{split}_{i}" : [generate_synthetic_language(t["re"])]
                for i, t in enumerate(raw_split[:n_tasks])
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