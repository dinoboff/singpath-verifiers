import java.util.ArrayList;
import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import org.json.simple.JSONObject;
import java.io.FileWriter;
import java.io.IOException;

public class TestRunner {
   public static void main(String[] args) throws IOException {
      ArrayList theResults = new ArrayList();
      
      Result result = JUnitCore.runClasses(SingPathTest.class);
      for (Failure failure : result.getFailures()) {
         //System.out.println(failure.toString());
         ArrayList resultLine = new ArrayList();
         resultLine.add(failure.toString());
         resultLine.add("");
         resultLine.add("");
         resultLine.add("fail");
         
         theResults.add(resultLine);
      }
      //System.out.println("Run count "+ result.getRunCount());
      //System.out.println("Run time "+ result.getRunTime());
      //System.out.println("Successful "+ result.wasSuccessful());
    
      JSONObject obj=new JSONObject();

      obj.put("run_count", result.getRunCount());
      obj.put("run_time", result.getRunTime());
      obj.put("solved", result.wasSuccessful());
      obj.put("results", theResults);
      //SingPath verifier response format
      //{"results": [["fib(5)", 51, "13", "fail"], ["fib(1)", 1, "1", "pass"], ["fib(8)", 21, "55", "fail"]]}
      
      // Save the results to results.json
      FileWriter file = new FileWriter("results.json");
        try {
            file.write(obj.toJSONString()); 
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            file.flush();
            file.close();
        }

   }
} 