import subprocess
from config import *
from colorama import Fore, Style, init
import os


class TestRunner:

    def __init__(self, test_path, target_path, test_file_name, package, class_name, tool="cobertura"):
        self.coverage_tool = tool
        self.test_path = test_path
        self.target_path = target_path
        self.test_file_name = test_file_name
        self.package = package
        self.class_name = class_name
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.deps_dir = os.path.join(self.repo_root, "dependencies", "lib", "*")

    def compile_test(self):
        try:
            is_compiled = False
            logs = ""

            # Define your commands
            commands = [
                "javac -target 11 -source 11 -cp target/classes:{}:evosuite-tests {}".format(self.deps_dir, self.test_file_name)
            ]

            # COMPILING
            print("cmd: " + Fore.GREEN + commands[0], Style.RESET_ALL)
            success, logs = self.run_command_with_timeout(commands[0], working_directory=self.target_path, timeout=120)
            if success:
                print("Compile: " + Fore.GREEN + "SUCCESS", Style.RESET_ALL)
                is_compiled = True
            else:
                print("Compile: " + Fore.RED + "FAIL", Style.RESET_ALL)

            return is_compiled, logs
        except Exception as e:
            print(e)
            return False, str(e)

    def compile_with_maven(self, project_root, clean=True, skip_tests=True, timeout=300):
        """
        Compile the project using Maven.

        :param clean: Whether to run 'mvn clean compile' instead of just 'mvn compile'
        :param skip_tests: Whether to skip tests during compilation
        :param timeout: Timeout in seconds
        :return: (is_compiled: bool, logs: str)

        Args:
            project_root:
        """
        try:
            is_compiled = False

            # Build Maven command
            base_cmd = "mvn"
            if clean:
                base_cmd += " clean"

            base_cmd += " compile"

            if skip_tests:
                base_cmd += " -DskipTests"

            print("cmd: " + Fore.GREEN + base_cmd, Style.RESET_ALL)

            success, logs = self.run_command_with_timeout(
                base_cmd,
                working_directory=project_root,
                timeout=timeout
            )

            if success:
                print("Maven Compile: " + Fore.GREEN + "SUCCESS", Style.RESET_ALL)
                is_compiled = True
            else:
                print("Maven Compile: " + Fore.RED + "FAIL", Style.RESET_ALL)

            return is_compiled, logs

        except Exception as e:
            print(e)
            return False, str(e)

    def run_test(self):
        try:
            is_run = False
            run_logs = ""

            # Define your commands
            commands = [
                "java -cp target/classes:{}:evosuite-tests org.junit.runner.JUnitCore {}.{}".format(self.deps_dir, self.package, self.class_name)
            ]

            # RUNNING
            print("cmd: " + Fore.GREEN + commands[0], Style.RESET_ALL)
            success_r, run_logs = self.run_command_with_timeout(commands[0], working_directory=self.target_path,
                                                                timeout=120)
            if success_r:
                print("RUN: " + Fore.GREEN + "SUCCESS", Style.RESET_ALL)
                is_run = True
            else:
                print("RUN: " + Fore.RED + "FAIL", Style.RESET_ALL)

            # Returning logs as a dictionary or concatenated string is common;
            # here we return them as separate elements in the tuple.
            return is_run, run_logs
        except Exception as e:
            print(e)
            return None, str(e)

    def run_command(self, command, working_directory=None):
        try:
            # Added capture_output=True and text=True to match the behavior of the timeout version
            result = subprocess.run(command, shell=True, check=True, cwd=working_directory, capture_output=True,
                                    text=True)
            # print(f"Command '{command}' executed successfully.")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error executing command '{command}': {e}")
            return False, e.stderr

    def run_command_with_timeout(self, command, working_directory=None, timeout=None):
        """
        Modified to capture output and return (Success, Output/Error)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_directory,
                timeout=timeout,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired as e:
            print(f"Command '{command}' timed out: {e}. Retrying...")
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=working_directory,
                    timeout=timeout,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, result.stdout
                else:
                    return False, result.stderr
            except subprocess.TimeoutExpired as e:
                print(f"Retrying command '{command}' also timed out: {e}")
                return False, "TIMEOUT"
            except Exception as e:
                print(f"Error executing command on retry '{command}': {e}")
                return False, str(e)
        except Exception as e:
            print(f"Error executing command '{command}': {e}")
            return False, str(e)