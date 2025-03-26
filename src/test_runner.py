import subprocess
from config import *
from colorama import Fore, Style, init


class TestRunner:

    def __init__(self, test_path, target_path, test_file_name, package, class_name, tool="cobertura"):
        self.coverage_tool = tool
        self.test_path = test_path
        self.target_path = target_path
        self.test_file_name = test_file_name
        self.package = package
        self.class_name = class_name

    def compile_and_run_test(self):
        try:
            is_compiled = False
            is_run = False
            mutation_score = 0
            
            # Define your commands
            commands = [
                # "mvn compile",
                # "export EVOSUITE='java -jar {}/evosuite-1.0.6.jar'".format(target_path),
                # "mvn dependency:copy-dependencies",
                # "java -version",
                # "export CLASSPATH=target/classes:evosuite-standalone-runtime-1.0.6.jar:evosuite-tests:target/dependency/junit-4.12.j/ar:target/dependency/hamcrest-core-1.3.jar",
                # "javac {}".format(test_path + "/*.java"),
                "javac -cp target/classes:/home/shaker/Documents/oracle_paper_v2/jars/*:evosuite-tests {}".format(self.test_file_name),
                "java -cp target/classes:/home/shaker/Documents/oracle_paper_v2/jars/*:evosuite-tests org.junit.runner.JUnitCore {}.{}".format(self.package, self.class_name)
                
                # "$EVOSUITE",
                # "$EVOSUITE -class tutorial.Stack -projectCP target/classes",
                # "javac evosuite-tests/tutorial/*.java",
                # "java org.junit.runner.JUnitCore tutorial.Stack_ESTest"
            ]
            
            # Run commands sequentially
            # for command in commands:
            #     if not self.run_command(command, working_directory=target_path):
            #         print("Command failed. Aborting.")
            #         break
            
            # COMPILING
            if self.run_command_with_timeout(commands[0], working_directory=self.target_path, timeout=120):
                # print("Compile: " + Fore.GREEN + "SUCCESS", Style.RESET_ALL)
                is_compiled = True
                
                # RUNNING
                if self.run_command_with_timeout(commands[1], working_directory=self.target_path, timeout=120):
                    # print("RUN: " + Fore.GREEN + "SUCCESS", Style.RESET_ALL)
                    is_run = True
                # else:
                    # print("RUN: " + Fore.RED + "FAIL", Style.RESET_ALL)
            # else:
                # print("Compile: " + Fore.RED + "FAIL", Style.RESET_ALL)
            
            return is_compiled, is_run, mutation_score
        except Exception as e:
            print(e)
            return None, None, None

    def run_command(self, command, working_directory=None):
        try:
            subprocess.run(command, shell=True, check=True, cwd=working_directory)
            # print(f"Command '{command}' executed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error executing command '{command}': {e}")
            return False
    
    def run_command_with_timeout(self, command, working_directory=None, timeout=None):
        try:
            subprocess.run(command, shell=True, check=True, cwd=working_directory, timeout=timeout)
            return True
        except subprocess.TimeoutExpired as e:
            print(f"Command '{command}' timed out: {e}. Retrying...")
            try:
                subprocess.run(command, shell=True, check=True, cwd=working_directory, timeout=timeout)
                return True
            except subprocess.TimeoutExpired as e:
                print(f"Retrying command '{command}' also timed out: {e}")
                return False
            except subprocess.CalledProcessError as e:
                print(f"Error executing command on retry '{command}': {e}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error executing command '{command}': {e}")
            return False
