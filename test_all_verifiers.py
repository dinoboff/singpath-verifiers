# This script downloads problem examples and runs them in a container.
# The initial development runs examples in a local directory until container execution can be implemented.  
import json
import os

"""
This script will need to be modified to write out problem.txt and solution.txt
The individual lanuage verifier.py files will be responisble for any file renaming and test file building. 
Loop through all of the examples and then find the needed files in each subfolder. 
Add the ability to pass in a specific language key. (java, python, javascript, angularjs, pandas, spark)
Make a loopback image as your first image whose verifier.py always writes out the same failing results.json

Find a developer with docker experience who can update the docker image with one that works. 

This script will mainly write out each problem and solution, run the docker verify command, collect the solution, 
and then compare the results.
You should be able to check all of the docker verifiers at once. 

There can be 2 scripts - run all of these from subfolders on the local machine after being unzipped. 
Then one to run all of these in the appropriate docker image. 
"""

# Todo: pass in verifier directory

# Write out tests from string
def write_solution(solution_code,  directory):        
    with open(directory+'/solution.txt', 'w') as the_file:
        the_file.write(solution_code)
        
def write_test(test_code, directory):
    with open(directory+'/tests.txt', 'w') as the_file:
        the_file.write(test_code)
        
def run_secure_verifier(directory):
    savedPath = os.getcwd()
    os.chdir(directory)
    os.system('python verify.py')
    os.chdir(savedPath)
    
def read_results(directory):
    with open(directory+'/results.json') as data_file:    
        results = json.load(data_file)
    return results

# Load problem examples
with open('problem_examples.json') as data_file:    
    examples = json.load(data_file)

# Iterterate through each language and call the language verify.py in each directory. 
test_results = {}
for language in examples.keys():
  if not test_results.has_key(language):
      test_results[language] = []  
  for key in examples[language].keys():
    example = examples[language][key]
    # write out problem.txt and tests.txt in the target directory. 
    write_solution(example['solution'], directory=language)
    write_test(example['tests'],  directory=language)
    
    # run the verifier. 
    run_secure_verifier( directory=language)
    result = read_results( directory=language)
    

    if result['solved'] != example['is_solved']:

        test_results[language].append("Failed - {} expected {} recieved {}.".format(key,example['is_solved'],result['solved']))
    else:
        test_results[language].append("Passed".format(key))

print("-----------------")
print("Problem Examples Test Results")
for language in test_results.keys(): 
    for result in test_results[language]: 
        print result


