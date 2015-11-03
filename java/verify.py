# This is the script intended to be run inside a secured docker container. 
# This script compiles and runs Java code. 

#Todo: Update the verifier to return JSON data rather than write it to a file. 

import json
import os
import subprocess
import shutil

# Script expects to to find TestRunner.java and/or TestRunner.class in the directory. 

junit_test_begin = """
import org.junit.Test;
import static org.junit.Assert.*;
import junit.framework.*;
public class SingPathTest extends TestCase {

public void testExample(){
//assertEquals(2 , 2);   
"""
read_only_directory = "data"
execution_directory = "java_data"


# Write out tests from string
def write_solution():
    #Open solution.txt and write solution out. 
    solution_code = ""
    with open('solution.txt', 'r') as solution:
        solution_code = solution.read()
        
    with open('SingPath.java', 'w') as the_file:
        the_file.write(solution_code)

def write_tests():
    #Open tests.txt and write tests out. 
    test_code = ""
    with open('tests.txt', 'r') as tests:
        test_code = tests.read()
    
    content = junit_test_begin + "\n" + test_code + "\n}\n}"
    
    with open('SingPathTest.java', 'w') as the_file:
        the_file.write(content)
            
def java_compile(): 
    #print("Compiling")
    fname = 'results.json'
    
    try:
        cmnd_output = subprocess.check_output('javac -cp "junit-4.10.jar:json-simple.jar" *.java',stderr=subprocess.STDOUT, shell=True)          
    except subprocess.CalledProcessError as exc:                                                                                                   
        return "Compile failed {}".format(exc.output)
    else:                                                                                                   
        pass
        #print("Output: \n{}\n".format(cmnd_output)) 
    
    # Return an empty string if no compile issues. 
    return ""
            
def junit_test():
    #print("Testing")
    os.system('java -cp ".:junit-4.10.jar:json-simple.jar" TestRunner')# > execute_output.txt')

def check_results():
    with open('results.json') as data_file:    
        data = json.load(data_file)
    #print("There are {} keys in the json output".format(len(data.keys())))
    #print("Verifier results were {}.".format(data['solved']))
    #print("Results {}".format(data['results']))
    return json.dumps(data)

# Copy data to a writable directory. 

shutil.copytree(read_only_directory, execution_directory)
# ---- switch to the data directory before starting. -----

os.chdir(execution_directory)

write_solution()
write_tests()
compile_result = java_compile()
#Check for compile result before Testing
if compile_result == "":
    junit_result = junit_test()
else: 
    # write out a standard compile error result. 
    data = {"errors": compile_result}
    with open("results.json", 'w') as outfile:
        json.dump(data, outfile) 

print(check_results())

