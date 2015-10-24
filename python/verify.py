import os
import logging
import doctest
import traceback
import json
import sys
#import StringIO
import io
from queue import Queue
import pwd
import re
    
def runPythonInstance(requestDict,outQueue):
    
    """ run a new  python instance and  test the code"""
    
    #laod json data in python object
    try:
        #print(requestDict)
        #print(requestDict.keys())
        jsonrequest = requestDict
        #print(jsonrequest)
        solution = str(jsonrequest["solution"])
        tests    = str(jsonrequest["tests"])
        #print(solution)
        #print(tests)
    except:
        responseDict = {'errors': 'Bad request'}
        logging.error("Bad request")
        responseJSON = json.dumps(responseDict)
        outQueue.put(responseJSON)
        return
    
    oldfile = sys.stdout
    sys.stdout = newfile =  io.StringIO()
    
    def ExecutionError():
        """ catch all the execution error, for the solution and each test """
        sys.stdout = oldfile
        errors = traceback.format_exc()
        logging.info("Python verifier returning errors =%s", errors)
        responseDict = {'errors': '%s' % errors}
        responseJSON = json.dumps(responseDict)
        outQueue.put(responseJSON) 
        
    try:
        # import numpy testing and execute solution 
        namespace = {}
        compiled = compile("", 'submitted code', 'exec')
        exec(compiled,namespace)
        compiled = compile(solution, 'submitted code', 'exec')
        exec(compiled,namespace)
        namespace['YOUR_SOLUTION'] = solution.strip()
        namespace['LINES_IN_YOUR_SOLUTION'] = len(solution.strip().splitlines())
    except:
        ExecutionError()
        return
    #get tests
    try:
        test_cases = doctest.DocTestParser().get_examples(tests)
    except:
        ExecutionError()
        return
    try:
        results,solved = execute_test_cases(test_cases, namespace)
    except:
        ExecutionError()
        return
        
    sys.stdout = oldfile
    printed = newfile.getvalue()
    
    responseDict = {"solved": solved , "results": results, "printed":printed}
    responseJSON = json.dumps(responseDict)
    logging.info("Python verifier returning %s",responseJSON)
    outQueue.put(responseJSON)

#Refactor for better readability.
def execute_test_cases(testCases, namespace):
    resultList = []
    solved = True
    
    for e in testCases:
        if not e.want:
            exec(e.source, namespace)
            continue
        call = e.source.strip()
        logging.warning('call: %s', (call,))
        got = eval(call, namespace)
        expected = eval(e.want, namespace)
        correct = True
        if got == expected:
            correct = True
        else:
            correct = False
            solved = False
        resultDict = {'call': call, 'expected': expected, 'received': "%(got)s" % {'got': got}, 'correct': correct}
        resultList.append(resultDict)
    return resultList, solved

def get_file_contents(target):
    #target = 'data/solution.txt'
    target_text = ""
    if os.path.exists(target):
        with open(target) as data_file:    
            target_text = data_file.read()
    return target_text

if __name__ == '__main__':
    out = Queue()
    # Find the tests at tests.txt and solutions at solution.txt
    solution = get_file_contents("data/solution.txt")
    tests = get_file_contents("data/tests.txt")
    #solution = "x=2"
    #tests = ">>> x\n 2"
    requestDict = {"tests": tests, "solution": solution}
    runPythonInstance(requestDict,out)
    print(out.get())