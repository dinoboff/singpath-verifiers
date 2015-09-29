# This script downloads problem examples and runs them in a container.
# The initial development runs examples in a local directory until container execution can be implemented.  
import json
import os
import sys

"""
This script will mainly write out each problem and solution, run the docker verify command, collect the solution, 
and then compare the results.
You should be able to check all of the docker verifiers at once. 

There can be 2 scripts - run all of these from subfolders on the local machine. 
Then one to run all of the problem in their docker containers. 
"""

run_in_containers = False

if len(sys.argv) > 1 and sys.argv[1]=='run_in_containers':
    print("Testing containers.")
    run_in_containers = True

docker_verifier_images = {}
#docker_verifier_images['java']= ""
#docker_verifier_images['python']= ""
#docker_verifier_images['javascript']= ""

# Write out tests from string
def write_solution(solution_code,  directory):        
    with open(directory+'/solution.txt', 'w') as the_file:
        the_file.write(solution_code)
        
def write_test(test_code, directory):
    with open(directory+'/tests.txt', 'w') as the_file:
        the_file.write(test_code)
        
def run_secure_verifier(directory):
    if run_in_containers:
        print("Container execution still under development.")
        # mount the directory to read problem.txt and solution.txt from. 
        # docker run java_conatainer python verify.py
        # read the results.json from container
        # shutdown ccontainer
        
    else: 
        # Test the verify.py scripts for each language in local subdirectories on a test system. 
        savedPath = os.getcwd()
        os.chdir(directory)
        os.system('python verify.py')
        os.chdir(savedPath)
    
def read_results(directory):
    target = directory+'/results.json'
    if os.path.exists(target):
        with open(target) as data_file:    
            results = json.load(data_file)
        return results
    else: 
        # Write out a no results returned error. 
        data = {"solved":False, 
                "results": [["Verifier did not return a result", 0, compile_result, "fail"]]}
        with open("results.json", 'w') as outfile:
            json.dump(data, outfile) 

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


