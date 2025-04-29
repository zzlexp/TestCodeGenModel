# coding=utf-8
"""
This script is used to create API-based coverage using combinatorial testing. 
Also, producing the selected apis based on the coverage
"""
from itertools import combinations
from multiprocessing import Pool
import itertools
import random
import os
import csv

def generate_combinations(args):
    fixed_element, rest_elements, k = args
    sub_k = k - 1
    if sub_k <= 0:
        return [(fixed_element,)] if k == 1 else []
    sub_combos = itertools.combinations(rest_elements, sub_k)
    return [(fixed_element,) + combo for combo in sub_combos]

def parallel_combinations(elements, k):
    # This functions is used to accelerate the generation of combinations
    elements = sorted(elements)
    n = len(elements)
    tasks = []
    for i in range(n - k + 1):
        fixed = elements[i]
        rest = elements[i+1:]
        tasks.append((fixed, rest, k))
    
    with Pool(os.cpu_count()) as pool:
        results = pool.map(generate_combinations, tasks)
    
    return set([combo for sublist in results for combo in sublist])

class CTAPICoverage(object):
    def __init__(self, apis_names_list, apis_details_list, n):
        self.apis_details_list = apis_details_list
        self.n = n
        # self.all_combinations = set(combinations(apis_names_list, n))
        self.all_combinations = parallel_combinations(apis_names_list, n)
        self.covered = set()
        self.uncovered = self.all_combinations - self.covered
    
    @classmethod
    def from_csv(cls, api_file_path, n):
        if not os.path.exists(api_file_path):
            raise FileNotFoundError(f"API file not found: {api_file_path}")

        apis_names_list = []
        apis_details_list = {}
        with open(api_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                apis_names_list.append(row['api_name'])
                apis_details_list[row['api_name']] = {
                    'description': row['description'], 
                        'parameters': row['parameters'], 
                        'examples': row['examples']
                }
        return cls(apis_names_list, apis_details_list, n)

    def generate_api_combination(self):
        """
        Return:
        target_apis_names: list: This is a list of api names in the current selected combination.
            For example:
            ['api_name1', 'api_name2', 'api_name3']
        target_apis_details: dict: This is the details of apis in the current selected combination.
            For example:
            {
                'api_name': {
                    'description': row['description'],
                        'parameters': row['parameters'],
                        'examples': row['examples']
                }
            }
        """
        target_apis_names = random.choice(tuple(self.uncovered)) if self.uncovered else None
        target_apis_details = {}
        for api_name in target_apis_names:
            target_apis_details[api_name] = self.apis_details_list[api_name]
        return target_apis_names, target_apis_details

    def calculate_coverage(self):
        total = len(self.all_combinations)
        covered = len(self.covered)
        return covered / total * 100 if total > 0 else 0.0

    def update_coverage(self, combination):
        if combination in self.all_combinations:
            self.covered.add(combination)
            self.uncovered.remove(combination)

if __name__ == "__main__":
    coverge = CTAPICoverage.from_csv("/home/test/program/TestCodeGenModel/lcmeval/crawler/numpy_apis/apis.csv", 1)
    init_coverage = coverge.calculate_coverage()
    assert init_coverage == 0.0
    target_apis_names, target_apis_details = coverge.generate_api_combination()
    print(f"The selected APIS are: {target_apis_names}")
    print(f"The details of selected APIS are: {target_apis_details}")
    coverge.update_coverage((target_apis_names))
    print(coverge.calculate_coverage())