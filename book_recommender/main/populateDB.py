from main.models import Libro
from bs4 import BeautifulSoup
import urllib.request
import os, ssl
from main.whoosh_index import update_index

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = "http://books.toscrape.com/catalogue/"

def populateDB():
    Libro.objects.all().delete()

    for page in range(1, 5):
        url = f"{BASE_URL}page-{page}.html"
        try:
            response = urllib.request.urlopen(url)
            soup = BeautifulSoup(response.read(), "lxml")
            books = soup.find_all("article", class_="product_pod")

            for book in books:
                try:
                    titulo = book.h3.a["title"]
                    precio = book.find("p", class_="price_color").get_text(strip=True)
                    disponibilidad = book.find("p", class_="instock availability").get_text(strip=True)
                    rating_class = book.p["class"]
                    rating = rating_class[1] if len(rating_class) > 1 else "None"

                    detalle_url = BASE_URL + book.h3.a["href"]
                    detalle_response = urllib.request.urlopen(detalle_url)
                    detalle_soup = BeautifulSoup(detalle_response.read(), "lxml")

                    categoria = detalle_soup.find("ul", class_="breadcrumb").find_all("li")[2].a.get_text(strip=True)
                    descripcion_tag = detalle_soup.find("div", id="product_description")
                    descripcion = descripcion_tag.find_next_sibling("p").get_text(strip=True) if descripcion_tag else "No disponible"

                    imagen_rel = detalle_soup.find("div", class_="item active").img["src"]
                    imagen_url = "http://books.toscrape.com/" + imagen_rel.replace("../..", "")

                    Libro.objects.create(
                        titulo=titulo,
                        precio=precio,
                        disponibilidad=disponibilidad,
                        categoria=categoria,
                        rating=rating,
                        descripcion=descripcion,
                        imagen_url=imagen_url
                    )
                except Exception as e:
                    print(f"No se pudo crear el libro: {e}")

        except Exception as e:
            print(f"No se pudo abrir la página {url}: {e}")
    update_index()

    print("Base de datos cargada correctamente.")
    return True
