from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from main.models import Libro, PuntuacionLibro

def recomendar_libros(libro_or_id, top_n=5):
    libros = list(Libro.objects.all())
    if not libros:
        return []

    docs = [f"{libro.categoria} {libro.descripcion}" for libro in libros]
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(docs)

    if isinstance(libro_or_id, Libro):
        libro_id = libro_or_id.id
    else:
        libro_id = libro_or_id

    indices = {libro.id: idx for idx, libro in enumerate(libros)}
    idx = indices.get(libro_id)
    if idx is None:
        return []

    cosine_sim = linear_kernel(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()
    similar_indices = cosine_sim.argsort()[::-1][1:top_n+1]
    return [libros[i] for i in similar_indices]
