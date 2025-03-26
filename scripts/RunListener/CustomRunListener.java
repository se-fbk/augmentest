import org.junit.runner.Description;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;
import java.util.Objects;
import org.junit.ComparisonFailure;

public class CustomRunListener extends RunListener {

    @Override
    public void testFailure(Failure failure) {
        if (Objects.nonNull(failure.getMessage())) {
            Throwable exception = failure.getException();
            
            if ((exception instanceof ComparisonFailure) || (exception instanceof AssertionError)) {
                System.out.println("##TEST_FAILURE_START##");
                System.out.println(failure.getDescription().getMethodName());
                System.out.println("##TEST_FAILURE_END##");
            } else {
                System.out.println("ERROR Type: " + exception.toString());
            }
        } else {
            System.out.println("TEST FAILED DUE TO AN ERROR");
        }
    }

    @Override
    public void testStarted(Description description) throws Exception {
        // System.out.println("Starting test: " + description.getMethodName());
    }

    @Override
    public void testFinished(Description description) throws Exception {
        System.out.println("Finished test: " + description.getMethodName());
    }

    @Override
    public void testIgnored(Description description) throws Exception {
        System.out.println("Ignored test: " + description.getMethodName());
    }
}
