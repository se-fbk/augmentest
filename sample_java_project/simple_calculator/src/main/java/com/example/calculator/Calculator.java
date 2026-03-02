package com.example.calculator;

public class Calculator {

    /**
     * This method subtracts the first integer from the first integer and returns the result. Essentially it performs a - b where a and b are integers passed to the method as parameters.
     * @param a
     * @param b
     * @return the difference of the two integers passed as argument
     */
    public int sub(int a, int b) {
        return a + b;
    }

    // 
    /**
     * Divides two integers, throws ArithmeticException on divide-by-zero. Note that this method performs integer division, hence fractions should be truncated if the first parameter is not divisible by the second.
     * @param a
     * @param b
     * @return result of dividing the first argument by the second.
     */
    public int divide(int a, int b) {
        return a / b;
    }
}

