""" Data utility """
import logging
import os
import requests
from os.path import join as pj

from datasets import load_dataset
from .language_model import internet_connection


__all__ = ('get_dataset', 'get_reference_files', 'DEFAULT_CACHE_DIR')
DEFAULT_CACHE_DIR = pj(os.path.expanduser('~'), '.cache', 'lmqg')


def get_dataset(path: str = 'asahi417/qg_squad',
                name: str = 'default',
                split: str = 'train',
                input_type: str = 'paragraph_answer',
                output_type: str = 'question',
                use_auth_token: bool = False):
    """ Get question generation input/output list of texts. """
    if name == 'default':
        dataset = load_dataset(path, split=split, use_auth_token=use_auth_token)
    else:
        dataset = load_dataset(path, name, split=split, use_auth_token=use_auth_token)
    return dataset[input_type], dataset[output_type]


def get_reference_files(path: str = 'lmqg/qg_squad', name: str = 'default', cache_dir: str = None):
    """ Get reference files for automatic evaluation """
    url = f'https://huggingface.co/datasets/{path}/raw/main/reference_files'
    local_files_only = not internet_connection()
    if cache_dir is None:
        cache_dir = pj(DEFAULT_CACHE_DIR, 'reference_files', path)
    output = {}
    for split in ['test', 'validation']:
        for feature in ['answer', 'question', 'paragraph', 'sentence', 'questions_answers']:
            if name == 'default':
                filename = f'{feature}-{split}.txt'
            else:
                filename = f'{feature}-{split}.{name}.txt'
            path = pj(cache_dir, filename)
            if os.path.exists(path):
                with open(path) as f:
                    line_length = len(f.read().split('\n'))
                if line_length < 20:
                    os.remove(path)
            if not os.path.exists(path):
                if local_files_only:
                    logging.info(f'network is not reachable, could not download the file from {url}/{filename}')
                    continue
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    r = requests.get(f'{url}/{filename}')
                    content = r.content
                    if "Entry not found" in str(content):
                        continue
                    f.write(content)
            with open(path) as f:
                line_length = len(f.read().split('\n'))
            if line_length < 20:
                os.remove(path)
                continue
            assert os.path.exists(path)
            output['{}-{}'.format(feature, split)] = path
    return output
