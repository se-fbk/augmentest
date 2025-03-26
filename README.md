# AugmenTest: AI-Powered Test Oracle Generation

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)

AugmenTest is an advanced automated test oracle generation system that leverages Large Language Models (LLMs) to enhance software testing efficiency. The tool generates JUnit test assertions and complete test cases, serving as an intelligent oracle for Java applications.

## Key Features

- 🧠 **LLM Integration**: Supports multiple LLM backends including GPT-4All and OpenAI
- 🧪 **Automated Assertion Generation**: Creates precise test assertions using code context
- 🔄 **Multi-Variant Prompting**: Implements different prompting strategies (Simple, Extended, RAG)
- 📊 **Test Augmentation**: Enhames existing EvoSuite-generated tests with intelligent oracles
- 🔍 **Context-Aware**: Utilizes code structure, developer comments, and dependencies

## Architecture Overview

![alt text](resources/evoOracle_overview.png)
*Figure 01: Tool Overview*

## Getting Started

### Prerequisites

- Python 3.8+
- Java 8+ (for EvoSuite integration)
- GPT4All or OpenAI API access

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/khandakerrahin/evooracle.git
   cd evooracle
   ```

2. Set up virtual environment:
   ```bash
   python -m venv augmentest_venv
   source augmentest_venv/bin/activate  # Linux/Mac
   .\augmentest_venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp config.ini.example config.ini
   # Edit config.ini with your paths and API keys
   ```

### Usage

1. **Preprocess Test Cases**:
   ```bash
   python run_preprocess_test_cases.py <project_dir> <language>
   # Example: python run_preprocess_test_cases.py /path/to/project java
   ```

2. **Generate Test Oracles**:
   ```bash
   python run_oracle_generation.py <test_id> <project_dir> <class_name> <method_name> <model> <variant> <use_comments>
   # Example: python run_oracle_generation.py T001 /path/to/project MyClass test1 Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf SIMPLE_PROMPT true
   ```

3. **Batch Processing** (for all test cases):
   ```bash
   python automate_pipeline.py /path/to/project java
   ```

## Configuration

Edit `config.ini` to customize:

```ini
[DEFAULT]
output_dir = ./output/
model_path = ./models/
openai_api_key = your-key-here
# ... other configurations
```

## Supported LLM Models

- Local Models:
  - Nous-Hermes-2-Mistral
  - Mistral-7B
  - GPT4All-J
- Cloud Models:
  - OpenAI GPT-3.5/4
  - Anthropic Claude

## Documentation

For detailed documentation, please see:
- [Architecture Design](docs/ARCHITECTURE.md)
- [Prompt Engineering Strategies](docs/PROMPTING.md)
- [Benchmark Results](docs/RESULTS.md)

## Contributing

We welcome contributions! Please see our [Contribution Guidelines](CONTRIBUTING.md).

## Citation

If you use AugmenTest in your research, please cite:

```bibtex
@misc{khandaker2025augmentestenhancingtestsllmdriven,
      title={AugmenTest: Enhancing Tests with LLM-Driven Oracles}, 
      author={Shaker Mahmud Khandaker and Fitsum Kifetew and Davide Prandi and Angelo Susi},
      year={2025},
      eprint={2501.17461},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2501.17461}, 
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Shaker Mahmud Khandaker  
📧 khandakerrahin@gmail.com  
🌐 [Personal Website](https://yourwebsite.com)