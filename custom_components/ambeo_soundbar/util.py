def find_title_by_id(id, search_list):
    """Find title by ID from a list."""
    for source in search_list:
        if source.get('id') == id:
            return source.get('title')
    return None

def find_id_by_title(title, search_list):
    """Find ID by title from a list."""
    for source in search_list:
        if source.get('title') == title:
            return source.get('id')
    return None
