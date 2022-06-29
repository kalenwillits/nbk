def string_to_file(file_string, file_path, encoder='LATIN'):
    with open(file_path, 'wb') as output_file:
        file_bytes = file_string.encode(encoder)
        output_file.write(file_bytes)
