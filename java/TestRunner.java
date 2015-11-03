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
         JSONObject myResult = new JSONObject();
         
         // This code is not watching for runtime exceptions. Need that test. 
         String[] parts = failure.toString().split(": expected:");
         String theCall = parts[0];
         String theRest = parts[1];
         
         String[] parts2 = theRest.split("but was:");
         String theExpected = parts2[0];
         String theReceived = parts2[1];
         
         myResult.put("expected", theExpected);
         myResult.put("call", theCall);
         myResult.put("received",theReceived );
         myResult.put("correct", false);
         theResults.add(myResult);     
             
      }
      //System.out.println("Run count "+ result.getRunCount());
      //System.out.println("Run time "+ result.getRunTime());
      //System.out.println("Successful "+ result.wasSuccessful());
    
      JSONObject obj=new JSONObject();

      obj.put("run_count", result.getRunCount());
      obj.put("run_time", result.getRunTime());
      obj.put("solved", result.wasSuccessful());
      // This should be different for errors. 
      obj.put("results", theResults);
      
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