import os
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID
from main.models import Libro

INDEX_DIR = "whoosh_index"

def update_index():
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)

    schema = Schema(
        id=ID(stored=True, unique=True),
        titulo=TEXT(stored=True),
        categoria=TEXT(stored=True)
    )

    if exists_in(INDEX_DIR):
        ix = open_dir(INDEX_DIR)
    else:
        ix = create_in(INDEX_DIR, schema)

    writer = ix.writer()


    for libro in Libro.objects.all():
        writer.update_document(
            id=str(libro.id),
            titulo=libro.titulo,
            categoria=libro.categoria
        )

    writer.commit()
    print("Índice de Whoosh actualizado correctamente.")
