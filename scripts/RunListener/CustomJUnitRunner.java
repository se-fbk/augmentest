import org.junit.runner.JUnitCore;
import org.junit.runner.Runner;
import org.junit.runner.notification.RunListener;
import org.junit.runner.notification.RunNotifier;

public class CustomJUnitRunner {

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java CustomJUnitRunner <test class name>");
            System.exit(1);
        }

        try {
            // Load the test class
            Class<?> testClass = Class.forName(args[0]);

            // Create an instance of JUnitCore
            JUnitCore core = new JUnitCore();
            
            // Create and add the custom RunListener
            RunListener listener = new CustomRunListener();
            core.addListener(listener);

            // Run the tests
            core.run(testClass);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }
}

