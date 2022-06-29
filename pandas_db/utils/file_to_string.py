def file_to_string(file_path, encoder='LATIN'):
    with open(file_path, 'rb') as file_bytes:
        file_string = file_bytes.read().decode(encoder)
        return file_string
