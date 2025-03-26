import requests

from pathlib import Path
from tqdm import tqdm

# model_name = 'ggml-gpt4all-l13b-snoozy.bin'
#model_name = 'ggml-mpt-7b-base.bin'
#model_name = 'ggml-gpt4all-j-v1.3-groovy.bin'
#model_name = 'ggml-mpt-7b-instruct.bin'
#model_name = 'ggml-stable-vicuna-13B.q4_2.bin'

# local_path = '/home/shaker/models/GPT4All/' + model_name  # replace with your desired local file path

def load_model(folder_name, model_name):
    local_path = f'{folder_name}/{model_name}'

    # Create the parent directory for the local file path if it doesn't exist
    Path(folder_name).mkdir(parents=True, exist_ok=True)

    # Check if the file already exists in the specified directory
    if Path(local_path).is_file():
        print(f'The model {model_name} already exists in the directory.')
        return

    print(f'The model {model_name} was not found. \nInitiating download. . .')
    # Construct the URL of the file using the model_name
    url = f'http://gpt4all.io/models/{model_name}'

    # Send a GET request to the URL with streaming enabled
    response = requests.get(url, stream=True)

    # Open the file in binary mode and write the contents of the response to it in chunks
    # This is a large file, so be prepared to wait
    with open(local_path, 'wb') as f:
        for chunk in tqdm(response.iter_content(chunk_size=8192)):
            if chunk:
                f.write(chunk)

    print(f'Downloaded {model_name} to {local_path}.')